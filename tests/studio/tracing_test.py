"""
This module does not test the actual exporting of traces to Studio, but rather the
tracing functionality itself and the traces that are created.
"""

import json
from typing import Any, Generator

import pytest
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
from pharia_skill.testing import DevCsi, MessageRecorder
from pharia_skill.testing.dev.client import CsiClient, Event

from .conftest import SpyExporter


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

    # And given a spy exporter
    spy = SpyExporter()
    stub_dev_csi.set_span_exporter(spy)

    # When running a message stream Skill
    haiku_stream(stub_dev_csi, MessageRecorder(), Input(topic="oat milk"))

    # Then we have received two spans
    assert len(spy.spans) == 2

    # And the chat spans are written to the chat span
    chat_span = spy.spans[0]
    assert chat_span.name == "chat_stream"
    assert chat_span.status.is_ok
    assert len(chat_span.events) == 3
    assert chat_span.events[1].attributes == {
        "content": "Hello, world!",
        "logprobs": (),
    }

    # And the output is written to the haiku span
    haiku_span = spy.spans[1]
    assert haiku_span.name == "haiku_stream"
    assert haiku_span.status.is_ok
    assert len(haiku_span.events) == 3

    assert chat_span.parent is not None
    assert chat_span.parent.span_id == haiku_span.context.span_id


def test_message_stream_result_is_traced(stub_dev_csi: DevCsi):
    # Given a message stream skill that returns multiple chat events
    events = [
        Event(event="message_begin", data={"role": "assistant"}),
        Event(event="message_append", data={"content": "Hello, ", "logprobs": []}),
        Event(event="message_append", data={"content": "world!", "logprobs": []}),
        Event(event="message_end", data={"finish_reason": "stop"}),
    ]
    stub_dev_csi.client.events = events  # type: ignore

    # And given a spy exporter
    spy = SpyExporter()
    stub_dev_csi.set_span_exporter(spy)

    # When running a message stream Skilla
    haiku_stream(stub_dev_csi, MessageRecorder(), Input(topic="oat milk"))

    # Then we have the skill output on the outer most span
    skill_span = spy.spans[1]
    assert skill_span.name == "haiku_stream"
    assert skill_span.attributes is not None
    assert (
        skill_span.attributes["output"]
        == '{"role":"assistant","content":"Hello, world!"}'
    )


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
    csi = DevCsi()
    csi.client = SaboteurCsiClient()
    return csi


def test_failing_csi_stream_usage_leads_to_error_span(saboteur_dev_csi: DevCsi):
    # Given a csi that raises an exception on every call
    spy = SpyExporter()
    saboteur_dev_csi.set_span_exporter(spy)

    # When running a skill
    with pytest.raises(RuntimeError, match="Out of cheese"):
        haiku_stream(saboteur_dev_csi, MessageRecorder(), Input(topic="oat milk"))

    # Then both, the csi and the skill span are marked as an error
    assert len(spy.spans) == 2
    assert not spy.spans[0].status.is_ok
    assert not spy.spans[1].status.is_ok


def test_csi_call_is_traced(stub_dev_csi: DevCsi):
    # Given a csi setup with an in-memory exporter
    spy = SpyExporter()
    stub_dev_csi.set_span_exporter(spy)

    # When running a completion request
    stub_dev_csi.complete(
        "llama-3.1-8b-instruct",
        "Say hello to Bob",
        CompletionParams(max_tokens=64),
    )

    # Then the exporter has received a successful span
    assert len(spy.spans) == 1
    first_span = spy.spans[0]
    assert first_span.status.is_ok

    # And the input and output are set as json attributes
    assert first_span.attributes is not None
    input = first_span.attributes["input"]
    assert isinstance(input, str)
    assert "Say hello to Bob" in json.loads(input)[0]["prompt"]

    output = first_span.attributes["output"]
    assert isinstance(output, str)
    assert json.loads(output)[0]["text"] == "Hello, world!"


def test_skill_is_traced(stub_dev_csi: DevCsi):
    # When running the skill with the dev csi
    spy = SpyExporter()
    stub_dev_csi.set_span_exporter(spy)
    haiku(stub_dev_csi, Input(topic="oat milk"))

    # Then the skill and the completion are traced
    assert len(spy.spans) == 3
    assert spy.spans[0].name == "search"
    assert spy.spans[1].name == "complete"
    assert spy.spans[2].name == "haiku"

    # And the traces are nested
    assert spy.spans[0].parent is not None
    assert spy.spans[0].parent.span_id == spy.spans[2].context.span_id


def test_csi_exception_is_traced(saboteur_dev_csi: DevCsi):
    # Given a csi with a failing complete
    spy = SpyExporter()
    saboteur_dev_csi.set_span_exporter(spy)

    # When the skill is invoked
    with pytest.raises(RuntimeError, match="Out of cheese"):
        haiku(saboteur_dev_csi, Input(topic="oat milk"))

    # Then the spans are collected by the studio collector
    assert len(spy.spans) == 3
    first, second, third = spy.spans
    assert first.name == "search"
    assert first.status.is_ok
    assert second.name == "complete"
    assert not second.status.is_ok
    assert third.name == "haiku"
    assert not third.status.is_ok


def test_stream_creation_exception_is_traced(saboteur_dev_csi: DevCsi):
    # Given a csi that raises an exception when a stream is created
    spy = SpyExporter()
    saboteur_dev_csi.set_span_exporter(spy)

    # When running a stream request
    with pytest.raises(RuntimeError, match="Out of cheese"):
        saboteur_dev_csi.chat_stream_step(
            "llama-3.1-8b-instruct", [Message.user("oat milk")], ChatParams()
        )

    # Then the spans are collected by the studio collector
    assert len(spy.spans) == 1
    assert not spy.spans[0].status.is_ok


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

    csi = DevCsi()
    csi.client = SaboteurStreamClient()
    spy = SpyExporter()
    csi.set_span_exporter(spy)

    # When running a chat stream request
    with pytest.raises(RuntimeError, match="Out of cheese"):
        with csi.chat_stream_step(
            "llama-3.1-8b-instruct", [Message.user("oat milk")], ChatParams()
        ) as response:
            list(response.stream())

    # Then the spans are collected by the studio collector
    assert len(spy.spans) == 1
    assert not spy.spans[0].status.is_ok


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
    spy = SpyExporter()
    stub_dev_csi.set_span_exporter(spy)

    # When doing a chat stream request
    with stub_dev_csi.chat_stream_step(
        "llama-3.1-8b-instruct", [Message.user("oat milk")], ChatParams()
    ) as response:
        list(response.stream())

    # Then the chat completion output is recorded on the span
    chat_span = spy.spans[0]
    assert chat_span.name == "chat_stream"
    assert chat_span.status.is_ok

    assert chat_span.attributes is not None
    output = chat_span.attributes["output"]
    assert isinstance(output, str)
    assert json.loads(output) == {
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
    spy = SpyExporter()
    stub_dev_csi.set_span_exporter(spy)

    # When doing a completion stream request
    with stub_dev_csi.completion_stream(
        "llama-3.1-8b-instruct", "How many fish in the sea?", CompletionParams()
    ) as response:
        list(response.stream())

    # Then the completion output is recorded on the span
    completion_span = spy.spans[0]
    assert completion_span.name == "completion_stream"
    assert completion_span.status.is_ok

    assert completion_span.attributes is not None
    output = completion_span.attributes["output"]
    assert isinstance(output, str)
    assert json.loads(output) == {
        "text": "Hello, world!",
        "finish_reason": "stop",
        "usage": {"prompt": 1, "completion": 1},
    }
