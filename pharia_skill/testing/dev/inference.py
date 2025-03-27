from collections.abc import Generator

from pydantic import BaseModel, RootModel, TypeAdapter
from sseclient import Event

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


class DevCompletionStreamResponse(CompletionStreamResponse):
    def __init__(self, stream: Generator[Event, None, None]):
        self._stream = stream

    def next(self) -> CompletionEvent | None:
        if event := next(self._stream, None):
            return completion_event_from_sse(event)
        return None


def completion_event_from_sse(event: Event) -> CompletionEvent:
    match event.event:
        case "append":
            return TypeAdapter(CompletionAppend).validate_json(event.data)
        case "end":
            return FinishReasonDeserializer.model_validate_json(
                event.data
            ).finish_reason
        case "usage":
            return TokenUsageDeserializer.model_validate_json(event.data).usage
        case "error":
            raise ValueError(event.data)
    raise ValueError(f"unknown event type: {event.event}")


class DevChatStreamResponse(ChatStreamResponse):
    def __init__(self, stream: Generator[Event, None, None]):
        self._stream = stream
        super().__init__()

    def next(self) -> ChatEvent | None:
        if event := next(self._stream, None):
            return chat_event_from_sse(event)
        return None


def chat_event_from_sse(event: Event) -> ChatEvent:
    match event.event:
        case "message_begin":
            role = RoleDeserializer.model_validate_json(event.data).role
            return MessageBegin(role)
        case "message_append":
            return TypeAdapter(MessageAppend).validate_json(event.data)
        case "message_end":
            return FinishReasonDeserializer.model_validate_json(
                event.data
            ).finish_reason
        case "usage":
            return TokenUsageDeserializer.model_validate_json(event.data).usage
        case "error":
            raise ValueError(event.data)
    raise ValueError(f"unknown event type: {event.event}")


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


CompletionRequestListSerializer = RootModel[list[CompletionRequest]]


CompletionListDeserializer = RootModel[list[Completion]]


ChatRequestListSerializer = RootModel[list[ChatRequest]]


ChatListDeserializer = RootModel[list[ChatResponse]]


ExplanationRequestListSerializer = RootModel[list[ExplanationRequest]]


ExplanationListDeserializer = RootModel[list[list[TextScore]]]
