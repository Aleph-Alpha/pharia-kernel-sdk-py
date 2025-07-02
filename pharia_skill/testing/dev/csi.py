"""
Translation between SDK types and the serialized format expected by the Pharia Kernel csi-shell endpoint.

While we could use the SDK types that we expose as part of the SDK for serialization/deserialization,
uncoupling these interfaces brings two advantages:

1. We can rename members at any time in the SDK (just a version bump) without requiring a new wit world / new version of the csi-shell.
2. We can use Pydantic models for serialization/deserialization without exposing these to the SDK users. We prefer dataclasses as they do not require keyword arguments for setup.
"""

import json
import warnings
from collections.abc import Generator
from typing import Any, Sequence

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.trace import StatusCode

from pharia_skill import (
    ChatParams,
    ChatRequest,
    ChatResponse,
    Chunk,
    ChunkRequest,
    Completion,
    CompletionParams,
    CompletionRequest,
    Csi,
    Document,
    DocumentPath,
    ExplanationRequest,
    InvokeRequest,
    JsonSerializable,
    Language,
    Message,
    SearchRequest,
    SearchResult,
    SelectLanguageRequest,
    TextScore,
    ToolResult,
)
from pharia_skill.csi.inference import (
    ChatStreamResponse,
    CompletionStreamResponse,
)
from pharia_skill.csi.inference.tool import Tool
from pharia_skill.studio import (
    StudioClient,
    StudioExporter,
    StudioSpanProcessor,
)

from .chunking import ChunkDeserializer, ChunkRequestSerializer
from .client import Client, CsiClient, Event
from .document_index import (
    DocumentDeserializer,
    DocumentMetadataDeserializer,
    DocumentMetadataSerializer,
    DocumentSerializer,
    SearchRequestSerializer,
    SearchResultDeserializer,
)
from .inference import (
    ChatListDeserializer,
    ChatRequestListSerializer,
    ChatRequestSerializer,
    CompletionListDeserializer,
    CompletionRequestListSerializer,
    CompletionRequestSerializer,
    DevChatStreamResponse,
    DevCompletionStreamResponse,
    ExplanationListDeserializer,
    ExplanationRequestListSerializer,
)
from .language import (
    SelectLanguageDeserializer,
    SelectLanguageRequestSerializer,
)
from .tool import (
    deserialize_tool_output,
    deserialize_tools,
    serialize_tool_requests,
)


class DevCsi(Csi):
    """
    The `DevCsi` can be used for testing Skill code locally against a running Pharia Kernel.

    This implementation of Cognitive System Interface (CSI) is backed by a running instance of Pharia Kernel via HTTP.
    This enables skill developers to run and test Skills against the same services that are used by the Pharia Kernel.

    Args:
        namespace: The namespace to use for tool invocations.
        project: The name of the studio project to export traces to.
            Will be created if it does not exist.

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

    * `PHARIA_STUDIO_ADDRESS` (Pharia Studio endpoint; example: "https://pharia-studio.product.pharia.com")
    """

    def __init__(
        self, namespace: str | None = None, project: str | None = None
    ) -> None:
        self.client: CsiClient = Client()
        self.namespace = namespace
        if project is not None:
            self._set_project(project)

    def _set_project(self, project: str) -> None:
        """Configure the `DevCsi` to export traces to Pharia Studio.

        This function creates a `StudioExporter` and registers it with the tracer provider.
        The exporter uploads spans once the root span ends.

        Args:
            project: The name of the studio project to export traces to. Will be created if it does not exist.
        """
        client = StudioClient.with_project(project)
        exporter = StudioExporter(client)
        self.set_span_exporter(exporter)

    @classmethod
    def with_studio(cls, project: str) -> "DevCsi":
        """Create a `DevCsi` that exports traces to Pharia Studio.

        This function creates a `StudioExporter` and registers it with the tracer provider.
        The exporter uploads spans once the root span ends.

        Args:
            project: The name of the studio project to export traces to. Will be created if it does not exist.
        """
        warnings.warn(
            "`DevCsi.with_studio` is deprecated. Use `DevCsi(project=...)` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        csi = cls()
        csi._set_project(project)
        return csi

    def invoke_tool_concurrent(
        self, requests: Sequence[InvokeRequest]
    ) -> list[ToolResult]:
        assert self.namespace is not None, (
            "Specifying a namespace when constructing a DevCsi is required when invoking tools"
        )
        body = serialize_tool_requests(namespace=self.namespace, requests=requests)
        output = self.run("invoke_tool", body)
        return deserialize_tool_output(output)

    def list_tools(self) -> list[Tool]:
        body = {"namespace": self.namespace}
        output = self.run("list_tools", body)
        return deserialize_tools(output)

    def _completion_stream(
        self, model: str, prompt: str, params: CompletionParams
    ) -> CompletionStreamResponse:
        body = CompletionRequestSerializer(
            model=model, prompt=prompt, params=params
        ).model_dump()
        function = "completion_stream"
        span = trace.get_tracer(__name__).start_span(function)
        span.set_attribute("input", json.dumps(body))
        events = self.stream(function, body, span)
        return DevCompletionStreamResponse(events, span)

    def _chat_stream(
        self, model: str, messages: list[Message], params: ChatParams
    ) -> ChatStreamResponse:
        body = ChatRequestSerializer(
            model=model, messages=messages, params=params
        ).model_dump()
        function = "chat_stream"
        span = trace.get_tracer(__name__).start_span(function)
        span.set_attribute("input", json.dumps(body))
        events = self.stream(function, body, span)
        return DevChatStreamResponse(events, span)

    def complete_concurrent(
        self, requests: Sequence[CompletionRequest]
    ) -> list[Completion]:
        body = CompletionRequestListSerializer(root=requests).model_dump()
        output = self.run("complete", body)
        return CompletionListDeserializer(root=output).root

    def chat_concurrent(self, requests: Sequence[ChatRequest]) -> list[ChatResponse]:
        body = ChatRequestListSerializer(root=requests).model_dump()
        output = self.run("chat", body)
        return ChatListDeserializer(root=output).root

    def explain_concurrent(
        self, requests: Sequence[ExplanationRequest]
    ) -> list[list[TextScore]]:
        body = ExplanationRequestListSerializer(root=requests).model_dump()
        output = self.run("explain", body)
        return ExplanationListDeserializer(root=output).root

    def chunk_concurrent(self, requests: Sequence[ChunkRequest]) -> list[list[Chunk]]:
        body = ChunkRequestSerializer(root=requests).model_dump()
        output = self.run("chunk_with_offsets", body)
        return ChunkDeserializer(root=output).root

    def select_language_concurrent(
        self, requests: Sequence[SelectLanguageRequest]
    ) -> list[Language | None]:
        body = SelectLanguageRequestSerializer(root=requests).model_dump()
        output = self.run("select_language", body)
        return SelectLanguageDeserializer(root=output).root

    def search_concurrent(
        self, requests: Sequence[SearchRequest]
    ) -> list[list[SearchResult]]:
        body = SearchRequestSerializer(root=requests).model_dump()
        output = self.run("search", body)
        return SearchResultDeserializer(root=output).root

    def documents_metadata(
        self, document_paths: Sequence[DocumentPath]
    ) -> list[JsonSerializable | None]:
        body = DocumentMetadataSerializer(root=document_paths).model_dump()
        output = self.run("document_metadata", body)
        return DocumentMetadataDeserializer(root=output).root

    def documents(self, document_paths: Sequence[DocumentPath]) -> list[Document]:
        body = DocumentSerializer(root=document_paths).model_dump()
        output = self.run("documents", body)
        return DocumentDeserializer(root=output).root

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
            span.set_attribute("output", json.dumps(output))

        return output

    def stream(
        self, function: str, data: dict[str, Any], span: trace.Span
    ) -> Generator[Event, None, None]:
        """Stream events from the client.

        While the `DevCsi` is responsible for tracing, streaming requires a different
        approach, because the `DevCsi` may already go out of scope, even if the
        completion has not been fully streamed. Therefore, the responsibility moves to
        the `DevChatStreamResponse` and `DevCompletionStreamResponse` classes.

        However, if an error occurs while constructing each one of these classes, we
        need to notify the span about the error in here.
        """
        try:
            events = self.client.stream(function, data)
        except Exception as e:
            span.set_status(StatusCode.ERROR, str(e))
            span.end()
            raise e

        for event in events:
            if event.event == "error":
                raise ValueError(event.data["message"])
            yield event
