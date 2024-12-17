from collections.abc import Sequence
from typing import Protocol

from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
    SpanExporter,
    SpanExportResult,
)

from pharia_skill.studio.span import StudioSpan


class SpanClient(Protocol):
    """Client that can submit spans.

    Separating the collection of spans from the uploading allows
    for better modularity and testability.
    """

    def submit_spans(self, spans: Sequence[StudioSpan]) -> None: ...


class StudioExporter(SpanExporter):
    """An OpenTelemetry exporter that uploads spans to Studio.

    The exporter will create a project on setup if it does not exist yet.
    It is generic over the client, allowing to decouple the collection
    from the uploading step.
    """

    def __init__(self, client: SpanClient):
        self.spans: dict[int, list[ReadableSpan]] = {}
        self.client = client

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        """Store spans in the exporter and upload them to Studio when the exporter shuts down.

        Studio is complaining about duplicate IDs when uploading traces with the same `span_id`
        in separate requests. Therefore, we store the spans and only flush when the root span ends.

        Args:
            spans (Sequence[ReadableSpan], required): stores a sequence of readable spans for upload
        """
        for span in spans:
            if span.context is None:
                raise ValueError("Span has no context")
            self._store_span(span)
            if span.parent is None:
                self._flush_trace(span.context.trace_id)

        return SpanExportResult.SUCCESS

    def _store_span(self, span: ReadableSpan) -> None:
        """Spans are grouped by trace_id for storage."""
        if span.context is None:
            raise ValueError("Span has no context")

        if (trace_id := span.context.trace_id) not in self.spans:
            self.spans[trace_id] = []
        self.spans[trace_id].append(span)

    def _flush_trace(self, trace_id: int) -> None:
        spans = self.spans.pop(trace_id)
        studio_spans = [StudioSpan.from_otel(span) for span in spans]
        self.client.submit_spans(studio_spans)

    def shutdown(self) -> None:
        """Will be called at the end of a session.

        There must not be any open spans left, all open spans should have been called with a parent,
        which has triggered the upload already.
        """
        assert len(self.spans) == 0, "No spans should be left in the exporter"
        self.spans.clear()


class StudioSpanProcessor(SimpleSpanProcessor):
    """Signal that a processor has been registered by the SDK."""

    pass
