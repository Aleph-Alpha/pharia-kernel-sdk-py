import pytest

from pharia_skill.csi.inference import (
    ChatParams,
    ChatStreamResponse,
    Message,
)
from pharia_skill.csi.tool import Tool
from pharia_skill.testing.stub import StubCsi


class SpyCsi(StubCsi):
    def __init__(self) -> None:
        self.chat_stream_messages: list[Message] = []

    def _chat_stream(
        self, model: str, messages: list[Message], params: ChatParams
    ) -> ChatStreamResponse:
        self.chat_stream_messages.extend(messages)
        return super()._chat_stream(model, messages, params)

    def list_tools(self) -> list[Tool]:
        return [
            Tool(name="dummy", description="my dummy", input_schema={}),
            Tool(name="dummy2", description="my dummy2", input_schema={}),
        ]


def test_chat_stream_adds_tools_to_system_prompt():
    # given a CSI
    csi = SpyCsi()

    # when listing tool schemas
    schemas = csi._list_tool_schemas(tools=["dummy"])

    # then only the tool schema is returned
    assert schemas == [Tool(name="dummy", description="my dummy", input_schema={})]


def test_chat_stream_raises_error_if_tool_not_available():
    # given a CSI
    csi = SpyCsi()

    # then the tool raises an error
    with pytest.raises(ValueError):
        # when listing tool schemas
        csi._list_tool_schemas(tools=["not_exist"])
