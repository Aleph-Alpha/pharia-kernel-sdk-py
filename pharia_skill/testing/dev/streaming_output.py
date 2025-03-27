from typing import Any

from pharia_skill.csi.streaming_output import MessageItem, Payload, Response


class DevResponse(Response):
    """A response that can be passed into a `message_stream` skill at testing time.

    It allows to inspect the output that a skill produces.

    Example::

        from pharia_skill import Csi, message_stream
        from pharia_skill.testing import Response, DevResponse

        @message_stream
        def my_skill(csi: Csi, response: DevResponse, input: Input) -> None:
            ...

        def test_my_skill():
            csi = DevCsi()
            response = DevResponse()
            input = Input(topic="The meaning of life")
            my_skill(csi, response, input)
            assert response.items == [
                MessageBegin(role="assistant"),
                MessageAppend(text="The meaning of life"),
                MessageEnd(payload=None),
            ]
    """

    def __init__(self) -> None:
        self.items: list[Any] = []

    def write(self, item: MessageItem[Payload]) -> None:
        self.items.append(item)
