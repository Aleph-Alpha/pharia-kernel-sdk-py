from collections.abc import Generator

from pharia_skill import ChatSession
from pharia_skill.csi import ChatParams, ChatStreamResponse, Message
from pharia_skill.csi.inference import ChatEvent, MessageBegin
from pharia_skill.csi.inference_types import MessageAppend
from pharia_skill.testing import StubCsi


class MockCsi(StubCsi):
    def _chat_stream(
        self, model: str, messages: list[Message], params: ChatParams
    ) -> ChatStreamResponse:
        class StubChatStreamResponse(ChatStreamResponse):
            def __init__(self, stream: Generator[ChatEvent, None, None]):
                self._stream = stream
                super().__init__()

            def next(self) -> ChatEvent | None:
                return next(self._stream, None)

        def generator() -> Generator[ChatEvent, None, None]:
            yield MessageBegin("assistant")
            yield MessageAppend("Hi, I'm an old ", logprobs=[])
            yield MessageAppend("fisherman, ", logprobs=[])
            yield MessageAppend("how are you?", logprobs=[])

        return StubChatStreamResponse(generator())


def test_chat_session_extends_history():
    # Given a chat session with an initial message
    csi = MockCsi()
    session = ChatSession(csi, "llama-3.1-8b-instruct")
    response = session.ask("Hello, how are you?")

    # When the response is consumed
    assert isinstance(response, Generator)
    list(response)

    # Then both messages are stored on the session
    assert len(session.messages) == 2
    assert session.messages[0].content == "Hello, how are you?"
    assert session.messages[1].content == "Hi, I'm an old fisherman, how are you?"
