from pydantic import BaseModel

from pharia_skill.csi import Logprob, Message, Role
from pharia_skill.csi.inference import (
    ChatEvent,
    ChatStreamResponse,
    MessageAppend,
    MessageBegin,
    ToolCall,
    ToolCallChunk,
    ToolCallEvent,
)
from pharia_skill.csi.inference.types import merge_tool_call_chunks


def test_serialized_roles_are_openai_compatible():
    class ChatInterface(BaseModel):
        messages: list[Message]

    message = Message.user("Hello, world!")
    input = ChatInterface(messages=[message])
    expected = '{"messages":[{"role":"user","content":"Hello, world!"}]}'
    assert input.model_dump_json(exclude_none=True) == expected


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
    tool_call = response.tool_calls()

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
        ToolCallEvent(tool_calls=[ToolCallChunk(index=0, id="abc", name="sea")]),
        ToolCallEvent(tool_calls=[ToolCallChunk(index=0, name="rch")]),
        ToolCallEvent(tool_calls=[ToolCallChunk(index=0, arguments='{"quer')]),
        ToolCallEvent(
            tool_calls=[
                ToolCallChunk(
                    index=0,
                    arguments='y": "2025 Giro de Italia last stage winning time"}',
                )
            ]
        ),
    ]
    response = MockChatStreamResponse(events)

    # When checking for a tool call
    tool_calls = response.tool_calls()

    # Then it should return the tool call
    assert tool_calls == [
        ToolCall(
            id="abc",
            name="search",
            arguments={"query": "2025 Giro de Italia last stage winning time"},
        )
    ]


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
    tool_call = response.tool_calls()

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
    response._peek()
    response._peek()

    # Then the stream should not have been altered
    assert response.role == Role.Assistant
    assert list(response.stream()) == [
        MessageAppend(content="Hello, ", logprobs=[]),
        MessageAppend(content="world!", logprobs=[]),
    ]


def test_message_helper():
    # Given a chat stream response that returns multiple events
    events: list[ChatEvent] = [
        MessageBegin(role="assistant"),
        MessageAppend(content="Hello, ", logprobs=[]),
        MessageAppend(content="world!", logprobs=[]),
    ]
    response = MockChatStreamResponse(events)

    # When using the message helper
    message = response.consume_message()

    # Then it should return the message
    assert message.role == Role.Assistant
    assert message.content == "Hello, world!"


def test_message_helper_after_stream_is_consumed():
    # Given a chat stream response that returns multiple events
    events: list[ChatEvent] = [
        MessageBegin(role="assistant"),
        MessageAppend(content="Hello, ", logprobs=[]),
        MessageAppend(content="world!", logprobs=[]),
    ]
    response = MockChatStreamResponse(events)

    # When consuming the stream and then using the message helper
    list(response.stream())
    message = response.consume_message()

    # Then no error is raised, but an empty message is returned
    assert message.role == Role.Assistant
    assert message.content == ""


def test_merge_tool_call_chunks():
    # Given a list of tool call chunks
    chunks = [
        ToolCallEvent(
            tool_calls=[
                ToolCallChunk(index=0, id="abc", name="add", arguments=""),
                ToolCallChunk(index=1, id="def", name="subtract", arguments=""),
            ]
        ),
        ToolCallEvent(
            tool_calls=[
                ToolCallChunk(index=0, arguments='{"'),
                ToolCallChunk(index=1, arguments='{"'),
            ]
        ),
        ToolCallEvent(
            tool_calls=[
                ToolCallChunk(index=0, arguments="first_ar"),
                ToolCallChunk(index=1, arguments="first_ar"),
            ]
        ),
        ToolCallEvent(
            tool_calls=[
                ToolCallChunk(index=0, arguments='gument"'),
                ToolCallChunk(index=1, arguments='gument"'),
            ]
        ),
        ToolCallEvent(
            tool_calls=[
                ToolCallChunk(index=0, arguments=':"1"}'),
                ToolCallChunk(index=1, arguments=':"2"}'),
            ]
        ),
    ]

    # When merging the tool call chunks
    tool_calls = merge_tool_call_chunks(chunks)

    # Then we get two tool calls
    assert len(tool_calls) == 2
    assert tool_calls[0].id == "abc"
    assert tool_calls[0].name == "add"
    assert tool_calls[0].arguments == {"first_argument": "1"}

    assert tool_calls[1].id == "def"
    assert tool_calls[1].name == "subtract"
    assert tool_calls[1].arguments == {"first_argument": "2"}


def test_can_merge_tool_call_chunks_with_no_chunks():
    # When merging an empty list of tool call chunks
    tool_calls = merge_tool_call_chunks([])

    # Then we get an empty list
    assert tool_calls == []


def test_name_spread_across_chunks():
    # Given a list of tool call chunks
    chunks = [
        ToolCallEvent(
            tool_calls=[
                ToolCallChunk(index=0, id="abc", name="a"),
                ToolCallChunk(index=1, id="def", name="su"),
            ]
        ),
        ToolCallEvent(
            tool_calls=[
                ToolCallChunk(index=0, name="dd", arguments="{}"),
                ToolCallChunk(index=1, name="btract", arguments="{}"),
            ]
        ),
    ]
    # When merging the tool call chunks
    tool_calls = merge_tool_call_chunks(chunks)

    # Then we get the tool calls
    assert len(tool_calls) == 2
    assert tool_calls[0].id == "abc"
    assert tool_calls[0].name == "add"
    assert tool_calls[0].arguments == {}

    assert tool_calls[1].id == "def"
    assert tool_calls[1].name == "subtract"
    assert tool_calls[1].arguments == {}
