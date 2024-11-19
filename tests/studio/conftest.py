import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
    SpanExporter,
    SpanExportResult,
)


class InMemorySpanExporter(SpanExporter):
    """An OpenTelemetry span exporter that stores spans in memory.

    Can be used for testing purposes.
    """

    def __init__(self):
        self.finished_spans = []

    def export(self, spans):
        self.finished_spans.extend(spans)
        return SpanExportResult.SUCCESS

    def shutdown(self):
        self.finished_spans.clear()


@pytest.fixture(scope="module")
def provider() -> TracerProvider:
    if not isinstance(trace.get_tracer_provider(), TracerProvider):
        trace_provider = TracerProvider()
        trace.set_tracer_provider(trace_provider)

    return trace.get_tracer_provider()  # type: ignore


@pytest.fixture
def exporter(provider: TracerProvider) -> InMemorySpanExporter:
    exporter = InMemorySpanExporter()
    span_processor = SimpleSpanProcessor(exporter)
    provider.add_span_processor(span_processor)
    return exporter
