from typing import Any, Generator

import pytest
from opentelemetry.sdk.trace import ReadableSpan
from pydantic import BaseModel

from pharia_skill import (
    CompletionParams,
    CompletionRequest,
    Csi,
    IndexPath,
    message_stream,
    skill,
)
from pharia_skill.csi import ChatParams, Message
from pharia_skill.message_stream.writer import MessageWriter
from pharia_skill.studio import StudioExporter
from pharia_skill.studio.span import SpanStatus
from pharia_skill.testing import DevCsi, MessageRecorder
from pharia_skill.testing.dev.client import CsiClient, Event

from .conftest import SpyClient


# Given a skill
class Input(BaseModel):
    topic: str


class Output(BaseModel):
    haiku: str


@skill
def haiku(csi: Csi, input: Input) -> Output:
    """Skill with two csi calls for tracing."""
    index = IndexPath("f13", "wikipedia-de", "luminous-base-asymmetric-64")
    csi.search(index, input.topic, 1, 0.5)

    request = CompletionRequest(
        model="llama-3.1-8b-instruct",
        prompt=input.topic,
        params=CompletionParams(max_tokens=64),
    )
    result = csi.complete_concurrent([request, request])
    return Output(haiku=result[0].text)


@message_stream
def haiku_stream(csi: Csi, writer: MessageWriter[Output], input: Input) -> None:
    """Do a chat stream and forward the response."""
    with csi.chat_stream_step(
        "llama-3.1-8b-instruct", [Message.user(input.topic)], params=ChatParams()
    ) as response:
        writer.forward_response(response)


def test_message_stream_is_traced(stub_dev_csi: DevCsi):
    # Given a csi which always streams these events
    events = [
        Event(event="message_begin", data={"role": "assistant"}),
        Event(
            event="message_append", data={"content": "Hello, world!", "logprobs": []}
        ),
        Event(event="message_end", data={"finish_reason": "stop"}),
    ]
    stub_dev_csi.client.events = events  # type: ignore

    # And given a spy client on the Studio exporter
    client = SpyClient()
    exporter = StudioExporter(client)
    stub_dev_csi.set_span_exporter(exporter)

    # When running a message stream Skill
    haiku_stream(stub_dev_csi, MessageRecorder(), Input(topic="oat milk"))

    # Then we have received one trace with two spans
    assert len(client.spans) == 1
    assert len(client.spans[0]) == 2

    # And the chat spans are written to the chat span
    chat_span = client.spans[0][0]
    assert chat_span.name == "chat_stream"
    assert chat_span.status == SpanStatus.OK
    assert len(chat_span.events) == 3
    assert chat_span.events[1].body == {"content": "Hello, world!", "logprobs": []}

    # And the output is written to the haiku span
    haiku_span = client.spans[0][1]
    assert haiku_span.name == "haiku_stream"
    assert haiku_span.status == SpanStatus.OK
    assert len(haiku_span.events) == 3

    assert chat_span.parent_id == haiku_span.context.span_id


def test_message_stream_result_is_traced(stub_dev_csi: DevCsi):
    # Given a message stream skill that returns multiple chat events
    events = [
        Event(event="message_begin", data={"role": "assistant"}),
        Event(event="message_append", data={"content": "Hello, ", "logprobs": []}),
        Event(event="message_append", data={"content": "world!", "logprobs": []}),
        Event(event="message_end", data={"finish_reason": "stop"}),
    ]
    stub_dev_csi.client.events = events  # type: ignore

    # And given a spy client on the Studio exporter
    client = SpyClient()
    exporter = StudioExporter(client)
    stub_dev_csi.set_span_exporter(exporter)

    # When running a message stream Skilla
    haiku_stream(stub_dev_csi, MessageRecorder(), Input(topic="oat milk"))

    # Then we have the skill output on the outer most span
    skill_span = client.spans[0][1]
    assert skill_span.name == "haiku_stream"
    assert skill_span.attributes.output == {
        "role": "assistant",
        "content": "Hello, world!",
    }


class SaboteurCsiClient(CsiClient):
    def run(self, function: str, data: Any) -> Any:
        match function:
            case "complete":
                raise RuntimeError("Out of cheese")
            case "search":
                return [[]]
            case _:
                return {}

    def stream(
        self, function: str, data: dict[str, Any]
    ) -> Generator[Event, None, None]:
        raise RuntimeError("Out of cheese")


@pytest.fixture
def saboteur_dev_csi() -> DevCsi:
    """Create a `DevCsi` that raises an exception on every call."""
    csi = DevCsi.__new__(DevCsi)
    csi.client = SaboteurCsiClient()
    return csi


def test_failing_csi_stream_usage_leads_to_error_span(saboteur_dev_csi: DevCsi):
    # Given a csi that raises an exception on every call
    client = SpyClient()
    exporter = StudioExporter(client)
    saboteur_dev_csi.set_span_exporter(exporter)

    # When running a skill
    with pytest.raises(RuntimeError, match="Out of cheese"):
        haiku_stream(saboteur_dev_csi, MessageRecorder(), Input(topic="oat milk"))

    # Then both, the csi and the skill span are marked as an error
    assert len(client.spans) == 1
    assert client.spans[0][0].status == SpanStatus.ERROR
    assert client.spans[0][1].status == SpanStatus.ERROR


def test_csi_call_is_traced(stub_dev_csi: DevCsi):
    # Given a csi setup with an in-memory exporter
    client = SpyClient()
    exporter = StudioExporter(client)
    stub_dev_csi.set_span_exporter(exporter)

    # When running a completion request
    stub_dev_csi.complete(
        "llama-3.1-8b-instruct",
        "Say hello to Bob",
        CompletionParams(max_tokens=64),
    )

    # Then the exporter has received a successful span
    assert len(client.spans) == 1
    assert client.spans[0][0].status == SpanStatus.OK

    # And the input and output are set as attributes
    assert "Say hello to Bob" in client.spans[0][0].attributes.input[0]["prompt"]
    output = client.spans[0][0].attributes.output
    assert output is not None
    assert output[0]["text"] == "Hello, world!"


def test_skill_is_traced(stub_dev_csi: DevCsi):
    # When running the skill with the dev csi
    client = SpyClient()
    exporter = StudioExporter(client)
    stub_dev_csi.set_span_exporter(exporter)
    haiku(stub_dev_csi, Input(topic="oat milk"))

    # Then the skill and the completion are traced
    assert len(client.spans) == 1
    assert client.spans[0][0].name == "search"
    assert client.spans[0][1].name == "complete"
    assert client.spans[0][2].name == "haiku"

    # And the traces are nested
    assert client.spans[0][0].parent_id == client.spans[0][2].context.span_id


def test_csi_exception_is_traced(saboteur_dev_csi: DevCsi):
    # Given a csi with a failing complete
    client = SpyClient()
    exporter = StudioExporter(client)
    saboteur_dev_csi.set_span_exporter(exporter)

    # When the skill is invoked
    with pytest.raises(RuntimeError, match="Out of cheese"):
        haiku(saboteur_dev_csi, Input(topic="oat milk"))

    # Then the spans are collected by the studio collector
    assert len(client.spans) == 1
    first, second, third = client.spans[0]
    assert first.name == "search"
    assert first.status == SpanStatus.OK
    assert second.name == "complete"
    assert second.status == SpanStatus.ERROR
    assert third.name == "haiku"
    assert third.status == SpanStatus.ERROR


def test_traces_are_exported_together(
    inner_span: ReadableSpan, outer_span: ReadableSpan
):
    # Given a csi with the studio exporter
    client = SpyClient()
    exporter = StudioExporter(client)

    # When we export the inner span
    exporter.export([inner_span])

    # And then the outer span
    exporter.export([outer_span])

    # Then the spans are submitted to the client
    assert len(client.spans) == 1
    assert len(client.spans[0]) == 2


def test_no_traces_exported_without_root_span(inner_span: ReadableSpan):
    # Given a csi with the studio exporter
    client = SpyClient()
    exporter = StudioExporter(client)

    # When we export a span without a root span
    exporter.export([inner_span])
    exporter.export([inner_span])

    # Then no traces are submitted
    assert len(client.spans) == 0


def test_inner_trace_is_matched_with_correct_parent(
    inner_span: ReadableSpan, error_span: ReadableSpan
):
    # Given a csi with the studio exporter
    client = SpyClient()
    exporter = StudioExporter(client)

    assert error_span.context is not None
    assert inner_span.context is not None
    assert error_span.context.trace_id != inner_span.context.trace_id

    # When we export two spans with different trace ids
    exporter.export([inner_span])
    exporter.export([error_span])

    # Then only the outer span is submitted
    assert len(client.spans) == 1
    assert len(client.spans[0]) == 1


def test_stream_creation_exception_is_traced(saboteur_dev_csi: DevCsi):
    # Given a csi that raises an exception when a stream is created
    client = SpyClient()
    exporter = StudioExporter(client)
    saboteur_dev_csi.set_span_exporter(exporter)

    # When running a stream request
    with pytest.raises(RuntimeError, match="Out of cheese"):
        saboteur_dev_csi.chat_stream_step(
            "llama-3.1-8b-instruct", [Message.user("oat milk")], ChatParams()
        )

    # Then the spans are collected by the studio collector
    assert len(client.spans) == 1
    assert client.spans[0][0].status == SpanStatus.ERROR


def test_exception_in_stream_item_is_traced():
    # Given a csi that raises an exception on the first stream item
    class SaboteurStreamClient(CsiClient):
        """A client that returns a stream, but then raises an exception later."""

        def run(self, function: str, data: Any) -> Any:
            raise NotImplementedError

        def stream(
            self, function: str, data: dict[str, Any]
        ) -> Generator[Event, None, None]:
            yield Event(event="message_begin", data={"role": "assistant"})
            raise RuntimeError("Out of cheese")

    client = SpyClient()
    exporter = StudioExporter(client)
    csi = DevCsi.__new__(DevCsi)
    csi.client = SaboteurStreamClient()
    csi.set_span_exporter(exporter)

    # When running a chat stream request
    with pytest.raises(RuntimeError, match="Out of cheese"):
        with csi.chat_stream_step(
            "llama-3.1-8b-instruct", [Message.user("oat milk")], ChatParams()
        ) as response:
            list(response.stream())

    # Then the spans are collected by the studio collector
    assert len(client.spans) == 1
    assert client.spans[0][0].status == SpanStatus.ERROR


def test_chat_stream_output_is_recorded(stub_dev_csi: DevCsi):
    # Given a message stream skill that does a completion
    events = [
        Event(event="message_begin", data={"role": "assistant"}),
        Event(event="message_append", data={"content": "Hello, ", "logprobs": []}),
        Event(event="message_append", data={"content": "world!", "logprobs": []}),
        Event(event="message_end", data={"finish_reason": "stop"}),
        Event(event="usage", data={"usage": {"prompt": 1, "completion": 1}}),
        Event(event="finish_reason", data={"finish_reason": "stop"}),
    ]
    stub_dev_csi.client.events = events  # type: ignore

    # And given a spy client on the Studio exporter
    client = SpyClient()
    exporter = StudioExporter(client)
    stub_dev_csi.set_span_exporter(exporter)

    # When doing a chat stream request
    with stub_dev_csi.chat_stream_step(
        "llama-3.1-8b-instruct", [Message.user("oat milk")], ChatParams()
    ) as response:
        list(response.stream())

    # Then the chat completion output is recorded on the span
    chat_span = client.spans[0][0]
    assert chat_span.name == "chat_stream"
    assert chat_span.status == SpanStatus.OK
    assert chat_span.attributes.output == {
        "message": {
            "role": "assistant",
            "content": "Hello, world!",
        },
        "finish_reason": "stop",
        "usage": {"prompt": 1, "completion": 1},
    }


def test_completion_stream_output_is_recorded(stub_dev_csi: DevCsi):
    # Given a message stream skill that does a completion
    events = [
        Event(event="append", data={"text": "Hello, ", "logprobs": []}),
        Event(event="append", data={"text": "world!", "logprobs": []}),
        Event(event="end", data={"finish_reason": "stop"}),
        Event(event="usage", data={"usage": {"prompt": 1, "completion": 1}}),
    ]
    stub_dev_csi.client.events = events  # type: ignore

    # And given a spy client on the Studio exporter
    client = SpyClient()
    exporter = StudioExporter(client)
    stub_dev_csi.set_span_exporter(exporter)

    # When doing a completion stream request
    with stub_dev_csi.completion_stream(
        "llama-3.1-8b-instruct", "How many fish in the sea?", CompletionParams()
    ) as response:
        list(response.stream())

    # Then the completion output is recorded on the span
    completion_span = client.spans[0][0]
    assert completion_span.name == "completion_stream"
    assert completion_span.status == SpanStatus.OK
    assert completion_span.attributes.output == {
        "text": "Hello, world!",
        "finish_reason": "stop",
        "usage": {"prompt": 1, "completion": 1},
    }
