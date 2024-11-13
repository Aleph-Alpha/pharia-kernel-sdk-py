import json

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
    SpanExporter,
    SpanExportResult,
)
from opentelemetry.trace import StatusCode
from pydantic import BaseModel

from pharia_skill import CompletionParams, Csi, skill
from pharia_skill.testing import DevCsi
from pharia_skill.testing.studio import StudioClient
from pharia_skill.testing.tracing import ExportedSpan, double_to_128bit


def test_convert_to_uuid():
    result = double_to_128bit("0xd1bf874f6554fe2b")
    assert str(result) == "d1bf874f-6554-fe2b-d1bf-874f6554fe2b"


def test_exported_span_from_inner(inner_span: dict):
    # Given a span created from `opentelemetry.sdk.trace.ReadableSpan.to_json()`
    # When the span is validated against the studio type `tracing.ExportedSpan`
    exported_span = ExportedSpan.model_validate(inner_span)

    # Then the span is validated successfully
    assert exported_span.name == "complete"

    # And can be dumped to json
    exported_span.model_dump_json()


def test_exported_span_from_outer_span(outer_span: dict):
    exported_span = ExportedSpan.model_validate(outer_span)
    assert exported_span.name == "haiku"
    exported_span.model_dump_json()


@pytest.fixture
def studio_client() -> StudioClient:
    """Ensure that a project exists and return a client.

    See the project at:

    https://pharia-studio.aleph-alpha.stackit.run/projects/786/traces
    """
    project = "kernel-test"
    studio_client = StudioClient(project=project)
    try:
        studio_client._get_project(project)
    except ValueError:
        studio_client.create_project(project)

    assert studio_client._get_project(project) is not None
    return studio_client


class InMemorySpanExporter(SpanExporter):
    def __init__(self):
        self.finished_spans = []

    def export(self, spans):
        self.finished_spans.extend(spans)
        return SpanExportResult.SUCCESS

    def shutdown(self):
        self.finished_spans.clear()


@pytest.fixture(scope="module")
def provider() -> TracerProvider:
    trace_provider = TracerProvider()
    trace.set_tracer_provider(trace_provider)
    return trace_provider


@pytest.fixture
def exporter(provider: TracerProvider) -> InMemorySpanExporter:
    exporter = InMemorySpanExporter()
    span_processor = SimpleSpanProcessor(exporter)
    provider.add_span_processor(span_processor)
    return exporter


@pytest.mark.kernel
def test_tracing(exporter: InMemorySpanExporter):
    # Given a csi setup with an in-memory exporter
    csi = DevCsi()

    # When running a completion request
    csi.complete(
        "llama-3.1-8b-instruct", "Say hello to Bob", CompletionParams(max_tokens=64)
    )

    # Then the exporter has received a successful span
    assert len(exporter.finished_spans) == 1
    assert exporter.finished_spans[0].status.status_code == StatusCode.OK

    # And the input and output are set as attributes
    assert "Say hello to Bob" in exporter.finished_spans[0].attributes["input"]
    assert "Bob" in exporter.finished_spans[0].attributes["output"]


# Given a skill
class Input(BaseModel):
    input: str


class Output(BaseModel):
    output: str


@skill
def haiku(csi: Csi, input: Input) -> Output:
    result = csi.complete(
        "llama-3.1-8b-instruct", input.input, CompletionParams(max_tokens=64)
    )
    return Output(output=result.text)


@pytest.mark.kernel
def test_skill_is_traced(exporter: InMemorySpanExporter):
    # When running the skill with the dev csi
    csi = DevCsi()
    haiku(csi, Input(input="oat milk"))

    # Then the skill and the completion are traced
    assert len(exporter.finished_spans) == 2
    assert exporter.finished_spans[0].name == "complete"
    assert exporter.finished_spans[1].name == "haiku"

    # And the traces are nested
    assert (
        exporter.finished_spans[0].parent.span_id
        == exporter.finished_spans[1].context.span_id
    )


@pytest.mark.kernel
def test_skill_run_uploads_to_studio(
    studio_client: StudioClient, exporter: InMemorySpanExporter
):
    # When running the skill with the dev csi
    csi = DevCsi()
    haiku(csi, Input(input="oat milk"))

    inner = ExportedSpan.model_validate(
        json.loads(exporter.finished_spans[0].to_json())
    )
    outer = ExportedSpan.model_validate(
        json.loads(exporter.finished_spans[1].to_json())
    )
    # When the span is uploaded to studio
    response = studio_client.submit_trace([inner, outer])

    # Then the trace_id is returned from the client
    assert response == str(outer.context.trace_id)
