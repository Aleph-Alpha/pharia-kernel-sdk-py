from pydantic import BaseModel, RootModel

from pharia_skill.csi import (
    ChatParams,
    ChatRequest,
    ChatResponse,
    Completion,
    CompletionParams,
    CompletionRequest,
)
from pharia_skill.csi.inference import (
    ExplanationRequest,
    FinishReason,
    Message,
    TextScore,
    TokenUsage,
)


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
