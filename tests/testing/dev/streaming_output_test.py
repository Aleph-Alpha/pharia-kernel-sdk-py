from pydantic import BaseModel

from pharia_skill import Csi
from pharia_skill.message_stream import message_stream
from pharia_skill.message_stream.writer import (
    MessageAppend,
    MessageBegin,
    MessageEnd,
    MessageWriter,
)
from pharia_skill.testing import StubCsi
from pharia_skill.testing.dev.streaming_output import MessageRecorder


def test_dev_response_can_be_used_to_test_skill_output():
    # Given a message stream skill
    class Input(BaseModel):
        topic: str

    @message_stream
    def my_skill(csi: Csi, writer: MessageWriter[None], input: Input) -> None:
        writer.begin_message("assistant")
        writer.append_to_message("The meaning of life")
        writer.end_message(payload=None)

    # When invoking it with the DevResponse
    csi = StubCsi()
    writer = MessageRecorder[None]()
    my_skill(csi, writer, Input(topic="The meaning of life"))

    # Then the items can be read from the DevResponse
    assert writer.items == [
        MessageBegin(role="assistant"),
        MessageAppend(text="The meaning of life"),
        MessageEnd(payload=None),
    ]
