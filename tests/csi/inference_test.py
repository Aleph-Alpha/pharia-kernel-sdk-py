from pydantic import BaseModel

from pharia_skill.csi.inference import (
    ChatEvent,
    ChatStreamResponse,
    CompletionAppend,
    CompletionEvent,
    CompletionStreamResponse,
    FinishReason,
    Logprob,
    Message,
    MessageAppend,
    MessageBegin,
    TokenUsage,
)


def test_serialized_roles_are_openai_compatible():
    class ChatInterface(BaseModel):
        messages: list[Message]

    message = Message.user("Hello, world!")
    input = ChatInterface(messages=[message])
    expected = '{"messages":[{"role":"user","content":"Hello, world!"}]}'
    assert input.model_dump_json() == expected


def test_logbprob_try_as_utf8():
    logprob = Logprob(token=b"Hi", logprob=1.0)
    assert logprob.try_as_utf8() == "Hi"


def test_logbprob_try_as_utf8_returns_none_for_invalid_utf8():
    logprob = Logprob(token=b"\x80", logprob=1.0)
    assert logprob.try_as_utf8() is None


class MockChatStreamResponse(ChatStreamResponse):
    def __init__(self, events: list[ChatEvent]):
        self.events = events
        self.index = 0
        super().__init__()

    def next(self) -> ChatEvent | None:
        if self.index < len(self.events):
            event = self.events[self.index]
            self.index += 1
            return event
        return None


def test_chat_stream_response_can_be_converted_to_message():
    # Given a chat stream response with multiple events
    events: list[ChatEvent] = [
        MessageBegin(role="assistant"),
        MessageAppend(content="Hello, ", logprobs=[]),
        MessageAppend(content="world!", logprobs=[]),
        FinishReason.STOP,
        TokenUsage(prompt=1, completion=1),
    ]
    stream = MockChatStreamResponse(events)

    # When the stream is converted to a message
    message = stream.message()

    # The the message is as expected
    assert message.role == "assistant"
    assert message.content == "Hello, world!"


class MockCompletionStreamResponse(CompletionStreamResponse):
    def __init__(self, events: list[CompletionEvent]):
        self.events = events
        self.index = 0
        super().__init__()

    def next(self) -> CompletionEvent | None:
        if self.index < len(self.events):
            event = self.events[self.index]
            self.index += 1
            return event
        return None


def test_completion_stream_can_be_converted_to_message():
    events: list[CompletionEvent] = [
        CompletionAppend(text="Hello, ", logprobs=[]),
        CompletionAppend(text="world!", logprobs=[]),
        FinishReason.STOP,
        TokenUsage(prompt=1, completion=1),
    ]
    stream = MockCompletionStreamResponse(events)

    # When the stream is converted to the content
    content = stream.text()

    # Then the content contains the expected text
    assert content == "Hello, world!"
