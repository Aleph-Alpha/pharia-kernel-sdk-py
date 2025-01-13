from dataclasses import dataclass
from typing import Literal

from .message import Message, Role
from .response import RawResponse, Response, SpecialTokens
from .tool import ToolCall


@dataclass
class AssistantMessage(Message):
    """A message that is returned from the LLM.

    With tool calling, the different messages diverge in their attributes,
    which is why they are represented by different classes.
    """

    role: Literal[Role.Assistant] = Role.Assistant
    tool_call: ToolCall | None = None
    content: str | None = None

    @classmethod
    def from_raw_response(cls, raw: RawResponse) -> "AssistantMessage":
        response = Response.from_raw(raw)
        tool_call = ToolCall.from_response(response)
        if tool_call is not None:
            return AssistantMessage(tool_call=tool_call)
        return AssistantMessage(content=response.text)

    def render(self) -> str:
        if self.tool_call is not None:
            return f"{self.role.render()}\n\n{self.tool_call.render()}{SpecialTokens.EndOfMessage.value}"
        return super().render()
