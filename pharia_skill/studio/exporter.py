import os
from collections.abc import Sequence
from typing import Optional, Protocol

from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
    SpanExporter,
    SpanExportResult,
)


class SpanClient(Protocol):
    """Client that can submit spans.

    Separating the collection of spans from the uploading allows
    for better modularity and testability.
    """

    def submit_spans(self, spans: Sequence[ReadableSpan]) -> None: ...


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
        # studio_spans = [StudioSpan.from_otel(span) for span in spans]
        # self.client.submit_spans(studio_spans)
        self.client.submit_spans(spans)

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


class OTLPStudioExporter(SpanExporter):
    """OTLP exporter configured for Studio backend.

    This exporter uses OpenTelemetry's OTLP HTTP/PROTOBUF exporter to send
    traces directly to Studio's traces_v2 endpoint.
    """

    def __init__(
        self,
        project_id: str,
        token: Optional[str] = None,
        endpoint: Optional[str] = None,
    ):
        """Initialize the OTLP Studio exporter.

        Args:
            project_id: The Studio project ID
            token: Authentication token (defaults to PHARIA_AI_TOKEN or AA_TOKEN env var)
            endpoint: Studio endpoint (defaults to PHARIA_STUDIO_ADDRESS env var)
        """
        # Get token from env if not provided
        if token is None:
            token = os.getenv("PHARIA_AI_TOKEN") or os.getenv("AA_TOKEN")
            if not token:
                raise ValueError(
                    "No authentication token provided. Set PHARIA_AI_TOKEN or AA_TOKEN environment variable."
                )

        # Get endpoint from env if not provided
        if endpoint is None:
            endpoint = os.getenv("PHARIA_STUDIO_ADDRESS", "http://localhost:8000")

        # Construct the full traces endpoint
        traces_endpoint = f"{endpoint}/api/projects/{project_id}/traces_v2"

        # Create the internal OTLP exporter
        self._otlp_exporter = OTLPSpanExporter(
            endpoint=traces_endpoint,
            headers={"Authorization": f"Bearer {token}"},
        )

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        """Export spans to Studio backend via OTLP.

        Args:
            spans: The spans to export

        Returns:
            The result of the export
        """
        return self._otlp_exporter.export(spans)

    def shutdown(self) -> None:
        """Shutdown the exporter."""
        return self._otlp_exporter.shutdown()

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        """Force flush any pending spans.

        Args:
            timeout_millis: The maximum amount of time to wait for spans to flush

        Returns:
            True if successful, False otherwise
        """
        # OTLPSpanExporter implements force_flush
        return self._otlp_exporter.force_flush(timeout_millis)


class LoggingOTLPExporter(SpanExporter):
    """A wrapper exporter that logs export operations for debugging."""

    def __init__(self, wrapped_exporter: SpanExporter, verbose: bool = True):
        """Initialize the logging wrapper.

        Args:
            wrapped_exporter: The actual exporter to wrap
            verbose: Whether to log verbose information
        """
        self.wrapped_exporter = wrapped_exporter
        self.verbose = verbose
        if self.verbose:
            print(f"Logging wrapper initialized for {type(wrapped_exporter).__name__}")

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        """Export spans and log the operation."""
        if self.verbose:
            trace_ids = {str(span.context.trace_id) for span in spans if span.context}
            print(
                f"🚀 Exporting batch of {len(spans)} spans with trace IDs: {', '.join(trace_ids)}"
            )

        result = self.wrapped_exporter.export(spans)

        if self.verbose:
            if result == SpanExportResult.SUCCESS:
                print("✅ Batch export successful")
            else:
                print(f"❌ Batch export failed: {result}")

        return result

    def shutdown(self) -> None:
        """Shutdown the wrapped exporter."""
        if self.verbose:
            print("Shutting down wrapped exporter")
        return self.wrapped_exporter.shutdown()
