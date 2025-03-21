from pydantic import BaseModel, RootModel

from pharia_skill.csi import (
    ChatRequest,
    ChatResponse,
    Completion,
    CompletionParams,
    CompletionRequest,
)
from pharia_skill.csi.inference import (
    ExplanationRequest,
    FinishReason,
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


class CompletionRequestListSerializer(BaseModel):
    requests: list[CompletionRequest]


CompletionListDeserializer = RootModel[list[Completion]]


class ChatRequestListSerializer(BaseModel):
    requests: list[ChatRequest]


ChatListDeserializer = RootModel[list[ChatResponse]]


class ExplanationRequestListSerializer(BaseModel):
    requests: list[ExplanationRequest]


ExplanationListDeserializer = RootModel[list[list[TextScore]]]
