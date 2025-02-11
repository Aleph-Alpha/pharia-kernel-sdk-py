from pydantic import BaseModel, RootModel

from pharia_skill.csi import ChatRequest, ChatResponse, Completion, CompletionRequest


class CompletionRequestSerializer(BaseModel):
    requests: list[CompletionRequest]


CompletionDeserializer = RootModel[list[Completion]]


class ChatRequestSerializer(BaseModel):
    requests: list[ChatRequest]


ChatDeserializer = RootModel[list[ChatResponse]]
