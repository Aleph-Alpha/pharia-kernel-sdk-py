import json
from collections.abc import Generator
from dataclasses import asdict
from types import TracebackType
from typing import Any, Sequence

from opentelemetry import trace
from opentelemetry.trace import StatusCode
from pydantic import BaseModel, RootModel, TypeAdapter

from pharia_skill import Role
from pharia_skill.csi.inference import (
    ChatEvent,
    ChatParams,
    ChatRequest,
    ChatResponse,
    ChatStreamResponse,
    Completion,
    CompletionAppend,
    CompletionEvent,
    CompletionParams,
    CompletionRequest,
    CompletionStreamResponse,
    ExplanationRequest,
    FinishReason,
    Message,
    MessageAppend,
    MessageBegin,
    TextScore,
    TokenUsage,
)
from pharia_skill.testing.dev.client import Event


class DevCompletionStreamResponse(CompletionStreamResponse):
    def __init__(self, stream: Generator[Event, None, None], span: trace.Span):
        self._stream = stream
        self.span = span
        self.tracing_buffer: list[CompletionEvent] = []
        super().__init__()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        if exc_type is not None:
            self.span.set_status(StatusCode.ERROR, str(exc_value))
        self.span.end()
        return super().__exit__(exc_type, exc_value, traceback)

    def next(self) -> CompletionEvent | None:
        """We can not rely on the user to consume the entire stream. Therefore,
        we need to update the span output on each iteration."""
        if event := next(self._stream, None):
            completion_event = completion_event_from_sse(event)
            self._record_span_event(completion_event)
            self._update_span_output()
            return completion_event

        self._update_span_output()
        return None

    def _record_span_event(self, event: CompletionEvent) -> None:
        self.tracing_buffer.append(event)

        match event:
            case CompletionAppend():
                attributes = unnest_attributes(asdict(event))
                self.span.add_event("completion_append", attributes=attributes)
            case TokenUsage():
                attributes = unnest_attributes(asdict(event))
                self.span.add_event("token_usage", attributes=attributes)
            case FinishReason():
                attributes = {"finish_reason": event.value}
                self.span.add_event("finish_reason", attributes=attributes)

    def _update_span_output(self) -> None:
        """Construct a `Completion` that can be stored for tracing."""
        text = "".join(
            [
                event.text
                for event in self.tracing_buffer
                if isinstance(event, CompletionAppend)
            ]
        )
        data: dict[str, Any] = {"text": text}
        if finish_reason := self._finish_reason_event():
            data["finish_reason"] = finish_reason.value
        if usage := self._token_usage_event():
            data["usage"] = asdict(usage)
        self.span.set_attribute("output", json.dumps(data))

    def _token_usage_event(self) -> TokenUsage | None:
        return next(
            (event for event in self.tracing_buffer if isinstance(event, TokenUsage)),
            None,
        )

    def _finish_reason_event(self) -> FinishReason | None:
        return next(
            (event for event in self.tracing_buffer if isinstance(event, FinishReason)),
            None,
        )


def completion_event_from_sse(event: Event) -> CompletionEvent:
    match event.event:
        case "append":
            return TypeAdapter(CompletionAppend).validate_python(event.data)
        case "end":
            return FinishReasonDeserializer.model_validate(event.data).finish_reason
        case "usage":
            return TokenUsageDeserializer.model_validate(event.data).usage
        case _:
            raise ValueError(f"Unexpected event type: {event.event}")


def unnest_attributes(data: dict[str, Any]) -> dict[str, str]:
    """
    OpenTelemetry only allows for one level of nesting in attributes, hence we flatten
    nested dicts to json strings.
    Studio itself would support arbitrary nesting (see `StudioSpan.events`), but as we use
    OpenTelemetry for tracing and only convert to Studio spans when exporting, we need to
    respect that limitation here.
    Another option would be to load these json strings into Python dicts in `StudioSpan.from_otel`.
    """
    return {k: json.dumps(v) if isinstance(v, dict) else v for k, v in data.items()}


class DevChatStreamResponse(ChatStreamResponse):
    """Development implementation of a chat stream response.

    This class takes care of tracing the chat stream events. A user might be interested
    in not only seeing the individual items, but also the entire response. Therefore, if
    the stream is consumed, this class records the items and tries to reconstruct the
    entire response, so it is available on the span.

    It can not create the trace object itself, as it does not know about the chat
    request, which we also want to trace. However, it takes over ownership and therefore
    also is responsible for ending the span and registering errors.

    For non-streaming request, the responsibility of tracing lies with the `DevCsi`.
    However, for constructing the response from individual items, knowledge about the
    event structure is needed, so the responsibility of tracing can not be taken over
    by the `DevCsi`.
    """

    def __init__(self, stream: Generator[Event, None, None], span: trace.Span):
        self._stream = stream
        self.span = span
        self.tracing_buffer: list[ChatEvent] = []
        super().__init__()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        if exc_type is not None:
            self.span.set_status(StatusCode.ERROR, str(exc_value))
        self.span.end()
        return super().__exit__(exc_type, exc_value, traceback)

    def _next(self) -> ChatEvent | None:
        """We can not rely on the user to consume the entire stream. Therefore,
        we need to update the span output on each iteration."""
        if event := next(self._stream, None):
            chat_event = chat_event_from_sse(event)
            self._record_span_event(chat_event)
            self._update_span_output()
            return chat_event

        # The last usage event is not part of the iterator, but sets the `_usage`
        # attribute, so we need to update the span output here.
        self._update_span_output()
        return None

    def _record_span_event(self, event: ChatEvent) -> None:
        self.tracing_buffer.append(event)

        match event:
            case MessageBegin():
                attributes = unnest_attributes(asdict(event))
                self.span.add_event("message_begin", attributes=attributes)
            case MessageAppend():
                attributes = unnest_attributes(asdict(event))
                self.span.add_event("message_append", attributes=attributes)
            case TokenUsage():
                attributes = unnest_attributes(asdict(event))
                self.span.add_event("token_usage", attributes=attributes)
            case FinishReason():
                attributes = {"finish_reason": event.value}
                self.span.add_event("finish_reason", attributes=attributes)

    def _update_span_output(self) -> None:
        """Construct a `ChatResponse` that can be stored for tracing.

        While a developer might be interested in the individual events of a stream,
        we also want to
        """
        # We can not do a lot without the first role event
        if getattr(self, "role", None) is not None:
            content = "".join(
                [
                    event.content
                    for event in self.tracing_buffer
                    if isinstance(event, MessageAppend)
                ]
            )
            message = Message(
                role=Role(self.role),
                content=content,
            )
            output: dict[str, Any] = {"message": asdict(message)}
            if finish_reason := self._finish_reason_event():
                output["finish_reason"] = finish_reason.value
            if usage := self._usage_event():
                output["usage"] = asdict(usage)
            self.span.set_attribute("output", json.dumps(output))

    def _finish_reason_event(self) -> FinishReason | None:
        return next(
            (event for event in self.tracing_buffer if isinstance(event, FinishReason)),
            None,
        )

    def _usage_event(self) -> TokenUsage | None:
        return next(
            (event for event in self.tracing_buffer if isinstance(event, TokenUsage)),
            None,
        )


def chat_event_from_sse(event: Event) -> ChatEvent:
    match event.event:
        case "message_begin":
            role = RoleDeserializer.model_validate(event.data).role
            return MessageBegin(role)
        case "message_append":
            return TypeAdapter(MessageAppend).validate_python(event.data)
        case "message_end":
            return FinishReasonDeserializer.model_validate(event.data).finish_reason
        case "usage":
            return TokenUsageDeserializer.model_validate(event.data).usage
        case _:
            raise ValueError(f"Unexpected event: {event}")


class FinishReasonDeserializer(BaseModel):
    finish_reason: FinishReason


class TokenUsageDeserializer(BaseModel):
    usage: TokenUsage


class CompletionRequestSerializer(BaseModel):
    model: str
    prompt: str
    params: CompletionParams


class ChatRequestSerializer(BaseModel):
    model: str
    messages: list[Message]
    params: ChatParams


class RoleDeserializer(BaseModel):
    role: str


CompletionRequestListSerializer = RootModel[Sequence[CompletionRequest]]


CompletionListDeserializer = RootModel[list[Completion]]


ChatRequestListSerializer = RootModel[Sequence[ChatRequest]]


ChatListDeserializer = RootModel[list[ChatResponse]]


ExplanationRequestListSerializer = RootModel[Sequence[ExplanationRequest]]


ExplanationListDeserializer = RootModel[list[list[TextScore]]]
