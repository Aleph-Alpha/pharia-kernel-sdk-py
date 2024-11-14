import pytest
from opentelemetry.trace import StatusCode
from pydantic import BaseModel

from pharia_skill import CompletionParams, Csi, skill
from pharia_skill.testing import DevCsi
from pharia_skill.testing.tracing import ExportedSpan, double_to_128bit

from .conftest import InMemorySpanExporter


def test_convert_to_uuid():
    result = double_to_128bit("0xd1bf874f6554fe2b")
    assert str(result) == "d1bf874f-6554-fe2b-d1bf-874f6554fe2b"


def test_exported_span_from_csi_call(inner_span: dict):
    # When validating a span created from tracing a csi call
    exported_span = ExportedSpan.model_validate(inner_span)

    # Then the span is validated successfully
    assert exported_span.name == "complete"

    # And can be dumped to json
    exported_span.model_dump_json()


def test_exported_span_from_skill(outer_span: dict):
    # When validating a span created from tracing a skill
    exported_span = ExportedSpan.model_validate(outer_span)

    # Then the span is validated successfully
    assert exported_span.name == "haiku"

    # And can be dumped to json
    exported_span.model_dump_json()


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
