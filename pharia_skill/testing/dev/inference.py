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


CompletionRequestListSerializer = RootModel[list[CompletionRequest]]


CompletionListDeserializer = RootModel[list[Completion]]


ChatRequestListSerializer = RootModel[list[ChatRequest]]


ChatListDeserializer = RootModel[list[ChatResponse]]


ExplanationRequestListSerializer = RootModel[list[ExplanationRequest]]


ExplanationListDeserializer = RootModel[list[list[TextScore]]]
