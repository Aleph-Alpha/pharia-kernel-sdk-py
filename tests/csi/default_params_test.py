from typing import Sequence

from pharia_skill.csi import (
    ChatParams,
    ChatRequest,
    ChatResponse,
    ChatStreamResponse,
)
from pharia_skill.csi.inference_types import Message
from pharia_skill.testing.stub import StubCsi


class SpyCsi(StubCsi):
    def __init__(self) -> None:
        self.chat_concurrent_requests: list[ChatRequest] = []
        self.chat_stream_params: list[ChatParams] = []

    def chat_concurrent(self, requests: Sequence[ChatRequest]) -> list[ChatResponse]:
        self.chat_concurrent_requests.extend(requests)
        return super().chat_concurrent(requests)

    def _chat_stream(
        self, model: str, messages: list[Message], params: ChatParams
    ) -> ChatStreamResponse:
        self.chat_stream_params.append(params)
        return super()._chat_stream(model, messages, params)


def test_chat_concurrent_default_params():
    csi = SpyCsi()
    csi.chat("llama-3.1-8b-instruct", [Message.user("Hello, world!")])
    assert len(csi.chat_concurrent_requests) == 1
    assert csi.chat_concurrent_requests[0].params == ChatParams()


def test_chat_stream_default_params():
    csi = SpyCsi()
    csi.chat_stream("llama-3.1-8b-instruct", [Message.user("Hello, world!")])
    assert len(csi.chat_stream_params) == 1
    assert csi.chat_stream_params[0] == ChatParams()
