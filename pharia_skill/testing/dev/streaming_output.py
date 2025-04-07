from dataclasses import asdict, dataclass
from typing import Generic

from opentelemetry import trace

from pharia_skill.message_stream.writer import (
    MessageAppend,
    MessageBegin,
    MessageEnd,
    MessageItem,
    MessageWriter,
    Payload,
)


@dataclass
class RecordedMessage(Generic[Payload]):
    role: str | None
    content: str = ""
    payload: Payload | None = None


class MessageRecorder(MessageWriter[Payload]):
    """A message writer that can be passed into a `message_stream` skill at testing time.

    It allows to inspect the output that a skill produces, either via the `items` property
    that stored individual chunks that have been written or via the `messages` method
    that aggregates the items into a list of messages.

    The MessageRecorder also validates the stream of items that are written to it.

    Example::

        from pharia_skill import Csi, message_stream, MessageAppend, MessageBegin, MessageEnd
        from pharia_skill.testing import MessageWriter, MessageRecorder, RecordedMessage

        @message_stream
        def my_skill(csi: Csi, writer: MessageWriter, input: Input) -> None:
            ...

        def test_my_skill():
            csi = DevCsi()
            writer = MessageRecorder()
            input = Input(topic="The meaning of life")

            my_skill(csi, writer, input)

            assert writer.messages() == [
                RecordedMessage(role="assistant", content="The meaning of life"),
            ]
    """

    def __init__(self) -> None:
        self.items: list[MessageItem[Payload]] = []
        self.span: trace.Span | None = None

    def write(self, item: MessageItem[Payload]) -> None:
        """Store and validate the streamed items.

        Validating the stream here gives the developer early feedback at test time.
        """
        # get current span and write an event
        if self.span is not None:
            match item:
                case MessageBegin():
                    self.span.add_event("message_begin", asdict(item))
                case MessageAppend():
                    self.span.add_event("message_append", asdict(item))
                case MessageEnd(payload=payload):
                    self.span.add_event(
                        "message_end",
                        {"payload": payload.model_dump_json()}
                        if payload is not None
                        else {},
                    )
        MessageRecorder.validate(self.items, item)
        self.items.append(item)

    @staticmethod
    def validate(
        existing: list[MessageItem[Payload]], item: MessageItem[Payload]
    ) -> None:
        """Is it legal to append this item to the previous items?

        There are three rules that must be followed:

        1. The first item must be a `MessageBegin`.
        2. Consecutive `MessageBegin`s must be preceded by a `MessageEnd`.
        3. A `MessageEnd` must not be preceded by `MessageEnd`.
        """

        if not existing:
            if not isinstance(item, MessageBegin):
                raise ValueError("The first item must be a `MessageBegin`")
            return

        if isinstance(item, MessageBegin) and not isinstance(existing[-1], MessageEnd):
            raise ValueError(
                "Consecutive `MessageBegin`s must be preceded by a `MessageEnd`"
            )

        if isinstance(item, MessageEnd) and isinstance(existing[-1], MessageEnd):
            raise ValueError(
                "A `MessageEnd` must not be preceded by another `MessageEnd`"
            )

    def messages(self) -> list[RecordedMessage[Payload]]:
        """Convenience method to aggregate the streamed items into a list of messages.

        Message items are validated when they are written, so we assume that the list is
        valid.
        """
        messages: list[RecordedMessage[Payload]] = []
        for item in self.items:
            match item:
                case MessageBegin(role=role):
                    messages.append(RecordedMessage(role=role))
                case MessageAppend(text=text):
                    messages[-1].content += text
                case MessageEnd(payload=payload):
                    messages[-1].payload = payload
        return messages
