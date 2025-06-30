from pydantic import BaseModel

from pharia_skill.csi import Logprob, Message, Role
from pharia_skill.csi.inference import (
    ChatEvent,
    ChatStreamResponse,
    MessageAppend,
    MessageBegin,
    ToolCallRequest,
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
    def __init__(self, events: list[ChatEvent]) -> None:
        self.events = events
        super().__init__()

    def _next(self) -> ChatEvent | None:
        if self.events:
            return self.events.pop(0)
        return None


def test_chat_stream_response_no_tool_call():
    # Given a chat stream response that returns multiple events
    events: list[ChatEvent] = [
        MessageBegin(role="assistant"),
        MessageAppend(content="Hello, ", logprobs=[]),
        MessageAppend(content="world!", logprobs=[]),
    ]
    response = MockChatStreamResponse(events)

    # When checking for a tool call
    tool_call = response.tool_call()

    # Then it should return None and the stream should yield all message append events
    assert tool_call is None
    assert list(response.stream()) == [
        MessageAppend(content="Hello, ", logprobs=[]),
        MessageAppend(content="world!", logprobs=[]),
    ]


def test_chat_stream_response_gives_tool_call_if_present():
    # Given a chat stream response that returns multiple events
    events: list[ChatEvent] = [
        MessageBegin(role="assistant"),
        MessageAppend(
            content='{"type": "function", "function": {"name": "search',
            logprobs=[],
        ),
        MessageAppend(
            content='", "parameters": {"query": "2025 Giro de Italia last stage winning time"}}}',
            logprobs=[],
        ),
    ]
    response = MockChatStreamResponse(events)

    # When checking for a tool call
    tool_call = response.tool_call()

    # Then it should return the tool call
    assert tool_call == ToolCallRequest(
        name="search",
        parameters={"query": "2025 Giro de Italia last stage winning time"},
    )


def test_empty_chat_stream_response_gives_none_for_tool_call():
    # Given a chat stream response that has already been streamed
    events: list[ChatEvent] = [
        MessageBegin(role="assistant"),
        MessageAppend(content="Hello, ", logprobs=[]),
        MessageAppend(content="world!", logprobs=[]),
    ]
    response = MockChatStreamResponse(events)
    list(response.stream())

    # When checking for a tool call
    tool_call = response.tool_call()

    # Then it should return None
    assert tool_call is None


def test_peeking_at_event_does_not_alter_stream():
    # Given a chat stream response that returns multiple events
    events: list[ChatEvent] = [
        MessageBegin(role="assistant"),
        MessageAppend(content="Hello, ", logprobs=[]),
        MessageAppend(content="world!", logprobs=[]),
    ]
    response = MockChatStreamResponse(events)

    # When peeking at the next event
    response.peek()
    response.peek()

    # Then the stream should not have been altered
    assert response.role == Role.Assistant
    assert list(response.stream()) == [
        MessageAppend(content="Hello, ", logprobs=[]),
        MessageAppend(content="world!", logprobs=[]),
    ]
