from pydantic import BaseModel

from pharia_skill import Csi
from pharia_skill.message_stream import message_stream
from pharia_skill.message_stream.response import (
    MessageAppend,
    MessageBegin,
    MessageEnd,
    Response,
)
from pharia_skill.testing import StubCsi
from pharia_skill.testing.dev.streaming_output import DevResponse


def test_dev_response_can_be_used_to_test_skill_output():
    # Given a message stream skill
    class Input(BaseModel):
        topic: str

    @message_stream
    def my_skill(csi: Csi, response: Response, input: Input) -> None:
        response.write(MessageBegin(role="assistant"))
        response.write(MessageAppend(text="The meaning of life"))
        response.write(MessageEnd(payload=None))

    # When invoking it with the DevResponse
    csi = StubCsi()
    response = DevResponse()
    my_skill(csi, response, Input(topic="The meaning of life"))

    # Then the items can be read from the DevResponse
    assert response.items == [
        MessageBegin(role="assistant"),
        MessageAppend(text="The meaning of life"),
        MessageEnd(payload=None),
    ]
