from pharia_skill.message_stream.writer import MessageItem, MessageWriter, Payload


class MessageRecorder(MessageWriter[Payload]):
    """A message writer that can be passed into a `message_stream` skill at testing time.

    It allows to inspect the output that a skill produces.

    Example::

        from pharia_skill import Csi, message_stream, MessageAppend, MessageBegin, MessageEnd
        from pharia_skill.testing import MessageWriter, MessageRecorder

        @message_stream
        def my_skill(csi: Csi, writer: MessageWriter, input: Input) -> None:
            ...

        def test_my_skill():
            csi = DevCsi()
            writer = MessageRecorder()
            input = Input(topic="The meaning of life")
            my_skill(csi, writer, input)
            assert writer.items == [
                MessageBegin(role="assistant"),
                MessageAppend(text="The meaning of life"),
                MessageEnd(payload=None),
            ]
    """

    def __init__(self) -> None:
        self.items: list[MessageItem[Payload]] = []

    def write(self, item: MessageItem[Payload]) -> None:
        self.items.append(item)
