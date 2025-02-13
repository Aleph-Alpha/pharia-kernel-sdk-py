"""
Translation between SDK types and the serialized format expected by the Pharia Kernel csi-shell endpoint.

While we could use the SDK types that we expose as part of the SDK for serialization/deserialization,
uncoupling these interfaces brings two advantages:

1. We can rename members at any time in the SDK (just a version bump) without requiring a new wit world / new version of the csi-shell.
2. We can use Pydantic models for serialization/deserialization without exposing these to the SDK users. We prefer dataclasses as they do not require keyword arguments for setup.
"""

import json
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.trace import StatusCode

from pharia_skill import (
    ChatRequest,
    ChatResponse,
    ChunkRequest,
    Completion,
    CompletionRequest,
    Csi,
    Document,
    DocumentPath,
    JsonSerializable,
    Language,
    SearchRequest,
    SearchResult,
    SelectLanguageRequest,
)
from pharia_skill.studio import (
    StudioClient,
    StudioExporter,
    StudioSpanProcessor,
)

from .chunking import ChunkDeserializer, ChunkRequestSerializer
from .client import Client, CsiClient
from .document_index import (
    DocumentDeserializer,
    DocumentMetadataDeserializer,
    DocumentMetadataSerializer,
    DocumentSerializer,
    SearchRequestSerializer,
    SearchResultDeserializer,
)
from .inference import (
    ChatDeserializer,
    ChatRequestSerializer,
    CompletionDeserializer,
    CompletionRequestSerializer,
)
from .language import (
    SelectLanguageDeserializer,
    SelectLanguageRequestSerializer,
)


class DevCsi(Csi):
    """
    The `DevCsi` can be used for testing Skill code locally against a running Pharia Kernel.

    This implementation of Cognitive System Interface (CSI) is backed by a running instance of Pharia Kernel via HTTP.
    This enables skill developers to run and test Skills against the same services that are used by the Pharia Kernel.

    Examples::

        # import your skill
        from haiku import run

        # create a `CSI` instance, optionally with trace export to Studio
        csi = DevCsi().with_studio("my-project")

        # Run your skill
        input = Input(topic="The meaning of life")
        result = run(csi, input)

        assert "42" in result.haiku

    The following environment variables are required:

    * `PHARIA_AI_TOKEN` (Pharia AI token)
    * `PHARIA_KERNEL_ADDRESS` (Pharia Kernel endpoint; example: "https://pharia-kernel.product.pharia.com")

    If you want to export traces to Pharia Studio, also set:

    * `PHARIA_STUDIO_ADDRESS` (Pharia Studio endpoint; example: "https://pharia-studio.aleph-alpha.stackit.run")
    """

    def __init__(self) -> None:
        self.client: CsiClient = Client()

    def complete_concurrent(
        self, requests: list[CompletionRequest]
    ) -> list[Completion]:
        body = CompletionRequestSerializer(requests=requests).model_dump()
        output = self.run("complete", body)
        return CompletionDeserializer(root=output).root

    def chat_concurrent(self, requests: list[ChatRequest]) -> list[ChatResponse]:
        body = ChatRequestSerializer(requests=requests).model_dump()
        output = self.run("chat", body)
        return ChatDeserializer(root=output).root

    def chunk_concurrent(self, requests: list[ChunkRequest]) -> list[list[str]]:
        body = ChunkRequestSerializer(requests=requests).model_dump()
        output = self.run("chunk", body)
        return ChunkDeserializer(root=output).root

    def select_language_concurrent(
        self, requests: list[SelectLanguageRequest]
    ) -> list[Language | None]:
        body = SelectLanguageRequestSerializer(requests=requests).model_dump()
        output = self.run("select_language", body)
        return SelectLanguageDeserializer(root=output).root

    def search_concurrent(
        self, requests: list[SearchRequest]
    ) -> list[list[SearchResult]]:
        body = SearchRequestSerializer(requests=requests).model_dump()
        output = self.run("search", body)
        return SearchResultDeserializer(root=output).root

    def documents_metadata(
        self, document_paths: list[DocumentPath]
    ) -> list[JsonSerializable | None]:
        body = DocumentMetadataSerializer(requests=document_paths).model_dump()
        output = self.run("document_metadata", body)
        return DocumentMetadataDeserializer(root=output).root

    def documents(self, document_paths: list[DocumentPath]) -> list[Document]:
        body = DocumentSerializer(requests=document_paths).model_dump()
        output = self.run("documents", body)
        return DocumentDeserializer(root=output).root

    @classmethod
    def with_studio(cls, project: str) -> "DevCsi":
        """Create a `DevCsi` that exports traces to Pharia Studio.

        This function creates a `StudioExporter` and registers it with the tracer provider.
        The exporter uploads spans once the root span ends.

        Args:
            project: The name of the studio project to export traces to. Will be created if it does not exist.
        """
        csi = cls()
        client = StudioClient.with_project(project)
        exporter = StudioExporter(client)
        csi.set_span_exporter(exporter)
        return csi

    @classmethod
    def set_span_exporter(cls, exporter: StudioExporter) -> None:
        """Set a span exporter for Studio if it has not been set yet.

        This method overwrites any existing exporters, thereby ensuring that there
        are never two exporters to Studio attached at the same time.
        """
        provider = cls.provider()
        for processor in provider._active_span_processor._span_processors:
            if isinstance(processor, StudioSpanProcessor):
                processor.span_exporter = exporter
                return

        span_processor = StudioSpanProcessor(exporter)
        provider.add_span_processor(span_processor)

    @classmethod
    def existing_exporter(cls) -> StudioExporter | None:
        """Return the first studio exporter attached to the provider, if any."""
        provider = cls.provider()
        for processor in provider._active_span_processor._span_processors:
            if isinstance(processor, StudioSpanProcessor):
                if isinstance(processor.span_exporter, StudioExporter):
                    return processor.span_exporter
        return None

    @staticmethod
    def provider() -> TracerProvider:
        """Tracer provider for the current thread.

        Check if the tracer provider is already set and if not, set it.
        """
        if not isinstance(trace.get_tracer_provider(), TracerProvider):
            trace_provider = TracerProvider()
            trace.set_tracer_provider(trace_provider)

        return trace.get_tracer_provider()  # type: ignore

    def run(self, function: str, data: dict[str, Any]) -> Any:
        with trace.get_tracer(__name__).start_as_current_span(function) as span:
            span.set_attribute("input", json.dumps(data))
            try:
                output = self.client.run(function, data)
            except Exception as e:
                span.set_status(StatusCode.ERROR, str(e))
                raise e
            span.set_status(StatusCode.OK)
            span.set_attribute("output", json.dumps(output))

        return output
