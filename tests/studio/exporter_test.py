from typing import Any, Sequence

import pytest
from opentelemetry.sdk.trace import ReadableSpan
from pydantic import BaseModel

from pharia_skill import (
    CompletionParams,
    CompletionRequest,
    Csi,
    IndexPath,
    skill,
)
from pharia_skill.studio import SpanClient, StudioClient, StudioExporter, StudioSpan
from pharia_skill.studio.span import SpanStatus
from pharia_skill.testing import DevCsi
from pharia_skill.testing.dev import CsiClient


class SpyClient(SpanClient):
    def __init__(self) -> None:
        self.spans: list[Sequence[StudioSpan]] = []

    def submit_spans(self, spans: Sequence[StudioSpan]):
        self.spans.append(spans)


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
    result = csi.complete_all([request, request])
    return Output(haiku=result[0].text)


class StubCsiClient(CsiClient):
    """Use the `DevCsi` without doing any http calls to the Kernel."""

    def run(self, function: str, data: Any) -> dict[str, Any] | list[dict[str, Any]]:
        completion = {"text": "Hello, world!", "finish_reason": "stop"}
        match function:
            case "complete":
                return [completion]
            case "search":
                return []
            case _:
                return {}


class SaboteurCsiClient(CsiClient):
    def run(self, function: str, data: Any) -> dict[str, Any] | list[dict[str, Any]]:
        match function:
            case "complete":
                raise RuntimeError("Out of cheese")
            case "search":
                return []
            case _:
                return {}


@pytest.fixture
def stub_dev_csi() -> DevCsi:
    """Create a `DevCsi` without requiring any env variables or setting up a session."""
    csi = DevCsi.__new__(DevCsi)
    csi.client = StubCsiClient()
    return csi


@pytest.fixture
def saboteur_dev_csi() -> DevCsi:
    """Create a `DevCsi` that raises an exception on every call."""
    csi = DevCsi.__new__(DevCsi)
    csi.client = SaboteurCsiClient()
    return csi


@pytest.mark.kernel
def test_trace_upload_studio_does_not_raise(stub_dev_csi: DevCsi):
    """Errors from uploading traces are handled by ErrorHandles.
    The default handling is silently ignoring the exceptions.

    Therefore, we explicitly collect the spans and upload them manually.
    """
    # Given a csi setup with the studio exporter
    client = SpyClient()
    exporter = StudioExporter(client)
    stub_dev_csi.set_span_exporter(exporter)

    # When running a skill and collecting spans
    haiku(stub_dev_csi, Input(topic="oat milk"))

    # Then no error is raised when running the skill
    StudioClient("kernel-test").submit_spans(client.spans[0])


def test_csi_call_is_traced(stub_dev_csi: DevCsi):
    # Given a csi setup with an in-memory exporter
    client = SpyClient()
    exporter = StudioExporter(client)
    stub_dev_csi.set_span_exporter(exporter)

    # When running a completion request
    stub_dev_csi.complete(
        "llama-3.1-8b-instruct", "Say hello to Bob", CompletionParams(max_tokens=64)
    )

    # Then the exporter has received a successful span
    assert len(client.spans) == 1
    assert client.spans[0][0].status == SpanStatus.OK

    # And the input and output are set as attributes
    input = client.spans[0][0].attributes.input
    assert "Say hello to Bob" in input["requests"][0]["prompt"]
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
