import datetime as dt
import json
from collections.abc import Generator
from types import TracebackType
from typing import Sequence

from opentelemetry import trace
from opentelemetry.trace import StatusCode
from pydantic import BaseModel, RootModel, TypeAdapter

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
from pharia_skill.csi.inference.types import Role
from pharia_skill.testing.dev.client import Event

LANGFUSE_COMPLETION_START_TIME = "langfuse.observation.completion_start_time"
"""Setting this attribute allows Langfuse to show the time to first token.

While it would be nice to have a more generic attribute name, this is not part of the
GenAI OTel conventions. Looking at the Langfuse codebase, they also check for the
`ai.response.msToFirstChunk` and `ai.stream.msToFirstChunk` attributes, which are
set by the Vercel SDK.
"""


class DevCompletionStreamResponse(CompletionStreamResponse):
    def __init__(self, stream: Generator[Event, None, None], span: trace.Span):
        self._stream = stream
        self.span = span
        self.text: str = ""
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
        """Development implementation of the `next` method.

        We can not rely on the user to consume the entire stream. Therefore, the span
        output is updated on iteration.
        """
        if (event := next(self._stream, None)) is None:
            # Ending the span here potentially conflicts with ending the span in the
            # `__exit__` method. However, not all users use this class as a context
            # manager, and we also want to end the span for them, and most span
            # implementations are forgiving about ending the span multiple times.
            self.span.end()
            return None

        completion_event = completion_event_from_sse(event)
        match completion_event:
            case CompletionAppend(text, _logprobs):
                if not self.text:
                    self.span.set_attribute(
                        LANGFUSE_COMPLETION_START_TIME,
                        json.dumps(dt.datetime.now(dt.UTC).isoformat()),
                    )
                self.text += text
            case TokenUsage():
                self.span.set_attributes(completion_event.as_gen_ai_otel_attributes())
            case FinishReason():
                self.span.set_attributes(completion_event.as_gen_ai_otel_attributes())

        self.span.set_attribute("gen_ai.content.completion", self.text)
        return completion_event


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


class DevChatStreamResponse(ChatStreamResponse):
    """Development implementation of a chat stream response.

    This class takes care of ensuring that individual stream items are mapped to the
    corresponding OTel GenAI conventions.

    Platforms like `Langfuse` render conversation messages nicely in the UI. A naive guess
    would be that, for streaming cases, they accumulate the assistant messages from
    individual events stored on teh span. However, that is not the case, so it is left
    up to the SDK to do this accumulation (similar logic can be found in the
    `_accumulate_stream_item` function in the `openllmetry` package).

    For non-streaming requests, the responsibility of tracing lies entirely within the
    `DevCsi`. However, to construct the response from individual items, knowledge
    about the event structure is needed, so some tracing responsibility needs to move
    into this class.

    However, the `DevChatStreamResponse` can not create the trace object itself, as it
    does not know about the chat request. As it takes over ownership of the span, it is
    also responsible for ending the span and registering errors.
    """

    def __init__(self, stream: Generator[Event, None, None], span: trace.Span):
        self._stream = stream
        self.span = span
        self.content_buffer: list[MessageAppend] = []
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
        """Development implementation of the `next` method.

        We can not rely on the user to consume the entire stream. Therefore, we need to
        update the span output on each iteration.
        """
        if (event := next(self._stream, None)) is None:
            # Ending the span here potentially conflicts with ending the span in the
            # `__exit__` method. However, not all users use this class as a context
            # manager, and we also want to end the span for them, and most span
            # implementations are forgiving about ending the span multiple times.
            self.span.end()
            return None

        chat_event = chat_event_from_sse(event)
        match chat_event:
            case MessageBegin():
                self.role = chat_event.role
            case MessageAppend():
                if not self.content_buffer:
                    self.span.set_attribute(
                        LANGFUSE_COMPLETION_START_TIME,
                        json.dumps(dt.datetime.now(dt.UTC).isoformat()),
                    )
                # accumulate the content so we can store the entire response on the span
                self.content_buffer.append(chat_event)
            case FinishReason():
                self.span.set_attributes(chat_event.as_gen_ai_otel_attributes())
            case TokenUsage():
                self.span.set_attributes(chat_event.as_gen_ai_otel_attributes())

        self._update_span_output()
        return chat_event

    def _update_span_output(self) -> None:
        """Construct the already received chat message and store it on the span."""
        if getattr(self, "role", None) is not None:
            message = Message(Role(self.role), self._received_content())
            self.span.set_attribute(
                "gen_ai.output.messages",
                json.dumps([message.as_gen_ai_otel_attributes()]),
            )

    def _received_content(self) -> str:
        """Accumulated content we have received so far."""
        return "".join([event.content for event in self.content_buffer])


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
