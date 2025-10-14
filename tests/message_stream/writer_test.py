from pydantic import BaseModel

from pharia_skill.csi import inference
from pharia_skill.message_stream.writer import (
    MessageAppend,
    MessageBegin,
    MessageEnd,
    MessageItem,
    MessageWriter,
    Reasoning,
)


class TestPayload(BaseModel):
    value: int


class TestWriter(MessageWriter[TestPayload]):
    def __init__(self) -> None:
        self.items: list[MessageItem[TestPayload]] = []

    def write(self, item: MessageItem[TestPayload]) -> None:
        self.items.append(item)


class StubChatStreamResponse(inference.ChatStreamResponse):
    def __init__(self, events: list[inference.ChatEvent]) -> None:
        self._events = events
        self._index = 0
        super().__init__()

    def _next(self) -> inference.ChatEvent | None:
        if self._index < len(self._events):
            event = self._events[self._index]
            self._index += 1
            return event
        return None


def test_forward_response():
    # Given a writer which stores the individual events it receives
    writer = TestWriter()

    # and given a stub chat stream response loaded with events
    events: list[inference.ChatEvent] = [
        inference.MessageBegin(role="assistant"),
        inference.MessageAppend(content="Hello, world!", logprobs=[]),
        inference.FinishReason.STOP,
        inference.TokenUsage(completion=1, prompt=0),
    ]
    response = StubChatStreamResponse(events)

    # When the writer gets a chat forward with a custom payload
    writer.forward_response(response, lambda r: TestPayload(value=r.usage().completion))

    # Then the writer stores the payload
    assert writer.items == [
        MessageBegin(role="assistant"),
        MessageAppend(text="Hello, world!"),
        MessageEnd(payload=TestPayload(value=1)),
    ]


def test_forward_reasoning_response():
    # Given a writer which stores the individual events it receives
    writer = TestWriter()

    # and given a stub chat stream response loaded with events
    events: list[inference.ChatEvent] = [
        inference.MessageBegin(role="assistant"),
        inference.Reasoning(content="Thinking..."),
    ]
    response = StubChatStreamResponse(events)

    # When the writer gets a chat forward with a custom payload
    writer.forward_response(response)

    # Then the writer stores the payload
    assert writer.items == [
        MessageBegin(role="assistant"),
        Reasoning(content="Thinking..."),
        MessageEnd(payload=None),
    ]


def test_does_not_forward_tool_call_events() -> None:
    # Given a writer which stores the individual events it receives
    writer = TestWriter()

    # and given a stub chat stream response loaded with events
    events: list[inference.ChatEvent] = [
        inference.MessageBegin(role="assistant"),
        inference.ToolCallEvent(tool_calls=[]),
    ]
    response = StubChatStreamResponse(events)

    # When the writer gets a chat forward with a custom payload
    writer.forward_response(response)

    # Then the writer stores the payload
    assert writer.items == [
        MessageBegin(role="assistant"),
        MessageEnd(payload=None),
    ]
