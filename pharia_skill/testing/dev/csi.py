"""
Translation between SDK types and the serialized format expected by the Pharia Kernel csi-shell endpoint.

While we could use the SDK types that we expose as part of the SDK for serialization/deserialization,
uncoupling these interfaces brings two advantages:

1. We can rename members at any time in the SDK (just a version bump) without requiring a new wit world / new version of the csi-shell.
2. We can use Pydantic models for serialization/deserialization without exposing these to the SDK users. We prefer dataclasses as they do not require keyword arguments for setup.
"""

import json
import os
from collections.abc import Generator
from typing import Any, Sequence

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.environment_variables import OTEL_EXPORTER_OTLP_ENDPOINT
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter
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
    InvokeRequest,
    JsonSerializable,
    Language,
    Message,
    SearchRequest,
    SearchResult,
    SelectLanguageRequest,
    Tool,
    ToolResult,
)
from pharia_skill.csi.inference import ChatStreamResponse, CompletionStreamResponse
from pharia_skill.studio import StudioClient
from pharia_skill.testing.dev.logfire import set_logfire_attributes

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
)
from .language import SelectLanguageDeserializer, SelectLanguageRequestSerializer
from .tool import deserialize_tool_output, deserialize_tools, serialize_tool_requests


class DevCsi(Csi):
    """The `DevCsi` can be used for testing Skill code locally against a PhariaKernel.

    This implementation of Cognitive System Interface (CSI) is backed by a running
    instance of PhariaKernel via HTTP. This enables Skill developers to run and test
    Skills against the same services that are used by the PhariaKernel.

    The `DevCsi` supports trace exports to different collectors. If you want to support
    traces to PhariaStudio, simply provide a project name on construction. If not set,
    a default exporter will be loaded from the corresponding environment variables.

    Args:
        namespace: The namespace to use for tool invocations.
        project: The name of the studio project to export traces to.
            Will be created if it does not exist.

    Examples::

        # import your skill
        from haiku import run

        # create a `CSI` instance, optionally with trace export to Studio
        csi = DevCsi(project="my-project")

        # Run your skill
        input = Input(topic="The meaning of life")
        result = run(csi, input)

        assert "42" in result.haiku

    The following environment variables are required:

    * `PHARIA_AI_TOKEN` (Pharia AI token)
    * `PHARIA_KERNEL_ADDRESS` (Pharia Kernel endpoint; example: "https://pharia-kernel.product.pharia.com")

    If you want to export traces to PhariaStudio, set:

    * `PHARIA_STUDIO_ADDRESS` (Pharia Studio endpoint; example: "https://pharia-studio.product.pharia.com")

    If you want to export traces to Langfuse, set:

    * `OTEL_EXPORTER_OTLP_ENDPOINT=https://cloud.langfuse.com/api/public/otel/v1/traces`
    * `OTEL_EXPORTER_OTLP_HEADERS` (Langfuse basic auth string; example: "Authorization=Basic ${AUTH_STRING}")

    See <https://langfuse.com/integrations/native/opentelemetry> on how to generate the
    basic auth string.
    """

    def __init__(
        self, namespace: str | None = None, project: str | None = None
    ) -> None:
        self.client: CsiClient = Client()
        self._namespace = namespace

        if project is not None:
            studio_client = StudioClient.with_project(project)
            self.set_span_exporter(studio_client.exporter())

        elif os.getenv(OTEL_EXPORTER_OTLP_ENDPOINT):
            self.set_span_exporter(OTLPSpanExporter())

    @classmethod
    def _with_client(cls, client: CsiClient) -> "DevCsi":
        """Create a `DevCsi` with a custom client, bypassing environment variable requirements.

        This is primarily useful for testing, where you can inject a mock client
        without needing to set up environment variables.
        """
        # Create instance without calling __init__ to avoid Client() construction
        instance = cls.__new__(cls)
        instance.client = client
        return instance

    def _namespace_or_raise(self) -> str:
        """Raise an error if the namespace is not set."""
        if self._namespace is None:
            raise ValueError(
                "Specifying a namespace when constructing the `DevCsi` is required when invoking or listing tools."
            )
        return self._namespace

    def invoke_tool_concurrent(
        self, requests: Sequence[InvokeRequest]
    ) -> list[ToolResult]:
        body = serialize_tool_requests(
            namespace=self._namespace_or_raise(), requests=requests
        )
        output = self.run("invoke_tool", body)
        return deserialize_tool_output(output)

    def list_tools(self) -> list[Tool]:
        body = {"namespace": self._namespace_or_raise()}
        output = self.run("list_tools", body)
        return deserialize_tools(output)

    def _completion_stream(
        self, model: str, prompt: str, params: CompletionParams
    ) -> CompletionStreamResponse:
        body = CompletionRequestSerializer(
            model=model, prompt=prompt, params=params
        ).model_dump()
        # See https://github.com/open-telemetry/semantic-conventions/blob/v1.37.0/docs/gen-ai/gen-ai-spans.md
        # for conventions around span names.
        span_name = f"text_completion {model}"
        span = trace.get_tracer(__name__).start_span(span_name)
        request = CompletionRequest(model, prompt, params)
        span.set_attributes(request.as_gen_ai_otel_attributes())
        events = self.stream("completion_stream", body, span)
        return DevCompletionStreamResponse(events, span)

    def _chat_stream(
        self,
        model: str,
        messages: list[Message],
        params: ChatParams,
    ) -> ChatStreamResponse:
        request = ChatRequest(model=model, messages=messages, params=params)
        body = ChatRequestSerializer(
            model=model, messages=messages, params=params
        ).model_dump()
        # See https://github.com/open-telemetry/semantic-conventions/blob/v1.37.0/docs/gen-ai/gen-ai-spans.md
        # for conventions around span names.
        span_name = f"chat {model}"
        span = trace.get_tracer(__name__).start_span(span_name)
        span.set_attributes(request.as_gen_ai_otel_attributes())
        events = self.stream("chat_stream", body, span)
        return DevChatStreamResponse(events, span, request)

    def chat_concurrent(self, requests: Sequence[ChatRequest]) -> list[ChatResponse]:
        """Generate model responses for a list of chat requests concurrently.

        This method adds GenAI specific tracing attributes to the span. Until we figure
        out how to do tracing for multiple requests, we can at least provide some GenAI
        specific attributes for the single request case.

        See <https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/#genai-attributes>
        for more details.
        """
        body = ChatRequestListSerializer(root=requests).model_dump()

        # See https://github.com/open-telemetry/semantic-conventions/blob/v1.37.0/docs/gen-ai/gen-ai-spans.md
        # for conventions around span names.
        span_name = f"chat {requests[0].model}" if len(requests) == 1 else "chat"
        with trace.get_tracer(__name__).start_as_current_span(span_name) as span:
            if len(requests) == 1:
                span.set_attributes(requests[0].as_gen_ai_otel_attributes())
            else:
                span.set_attribute("input", json.dumps(body))
            try:
                output = self.client.run("chat", body)
                response = ChatListDeserializer(root=output).root
            except Exception as e:
                span.set_status(StatusCode.ERROR, str(e))
                raise e
            if len(response) == 1:
                set_logfire_attributes(span, requests[0].messages, response[0].message)
                span.set_attributes(response[0].as_gen_ai_otel_attributes())
            else:
                span.set_attribute("output", json.dumps(output))
            return response

    def complete_concurrent(
        self, requests: Sequence[CompletionRequest]
    ) -> list[Completion]:
        """Generate model responses for a list of completion requests concurrently.

        This method adds GenAI specific tracing attributes to the span. Until we figure
        out how to do tracing for multiple requests, we can at least provide some GenAI
        specific attributes for the single request case.
        """
        body = CompletionRequestListSerializer(root=requests).model_dump()
        # See https://github.com/open-telemetry/semantic-conventions/blob/v1.37.0/docs/gen-ai/gen-ai-spans.md
        # for conventions around span names.
        span_name = (
            f"text_completion {requests[0].model}"
            if len(requests) == 1
            else "text_completion"
        )
        with trace.get_tracer(__name__).start_as_current_span(span_name) as span:
            if len(requests) == 1:
                span.set_attributes(requests[0].as_gen_ai_otel_attributes())
            else:
                span.set_attribute("input", json.dumps(body))
            try:
                output = self.client.run("complete", body)
                response = CompletionListDeserializer(root=output).root
            except Exception as e:
                span.set_status(StatusCode.ERROR, str(e))
                raise e
            if len(response) == 1:
                span.set_attributes(response[0].as_gen_ai_otel_attributes())
            else:
                span.set_attribute("output", json.dumps(output))
            return response

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
    def set_span_exporter(cls, exporter: SpanExporter) -> None:
        """Set a span exporter for Studio if it has not been set yet.

        This method overwrites any existing exporters, thereby ensuring that there
        are never two exporters to Studio attached at the same time.
        """

        provider = cls.provider()
        for processor in provider._active_span_processor._span_processors:
            if isinstance(processor, PhariaSkillProcessor):
                processor.span_exporter = exporter
                return

        span_processor = PhariaSkillProcessor(exporter)
        provider.add_span_processor(span_processor)

    @classmethod
    def existing_exporter(cls) -> SpanExporter | None:
        """Return the first exporter that has been set on the DevCsi."""
        provider = cls.provider()
        for processor in provider._active_span_processor._span_processors:
            if isinstance(processor, PhariaSkillProcessor):
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


class PhariaSkillProcessor(SimpleSpanProcessor):
    """Signal that a processor has been registered by the SDK."""

    pass
