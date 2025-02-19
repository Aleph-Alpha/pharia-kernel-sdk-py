from pydantic import BaseModel, RootModel

from pharia_skill.csi import ChatRequest, ChatResponse, Completion, CompletionRequest
from pharia_skill.csi.inference import ExplanationRequest, TextScore


class CompletionRequestSerializer(BaseModel):
    requests: list[CompletionRequest]


CompletionDeserializer = RootModel[list[Completion]]


class ChatRequestSerializer(BaseModel):
    requests: list[ChatRequest]


ChatDeserializer = RootModel[list[ChatResponse]]


class ExplanationRequestSerializer(BaseModel):
    requests: list[ExplanationRequest]


ExplanationDeserializer = RootModel[list[list[TextScore]]]
