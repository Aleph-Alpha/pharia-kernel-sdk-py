from pydantic import RootModel

from pharia_skill import Csi, skill
from pharia_skill.llama3 import ChatRequest, ChatResponse, chat


class ChatApi(RootModel[ChatRequest]):
    """Expose a chat api with function calling by forwarding a `ChatRequest`."""

    root: ChatRequest


class ChatOutput(RootModel[ChatResponse]):
    """The caller just receives one message back.

    State needs to be maintained on the caller side.
    """

    root: ChatResponse


@skill
def chat_api(csi: Csi, request: ChatApi) -> ChatOutput:
    """Expose a chat API with function calling"""
    response = chat(csi, request.root)
    return ChatOutput(root=response)
