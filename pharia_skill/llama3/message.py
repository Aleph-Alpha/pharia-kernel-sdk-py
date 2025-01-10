"""Take a chat request and convert it to a prompt"""

from dataclasses import dataclass
from enum import Enum

from .response import RawResponse, Response, SpecialTokens
from .tool import ToolCall, ToolResponse


class Role(str, Enum):
    """A role used for a message in a chat."""

    User = "user"
    Assistant = "assistant"
    System = "system"
    IPython = "ipython"

    @property
    def header(self) -> str:
        return f"<|start_header_id|>{self.value.lower()}<|end_header_id|>"


@dataclass
class Message:
    """Describes a message in a chat.

    Parameters:
        role (Role, required): The role of the message.
        content (str, required): The content of the message.
    """

    role: Role
    content: str | None
    tool_call: ToolCall | None = None
    tool_response: ToolResponse | None = None

    @classmethod
    def user(cls, content: str) -> "Message":
        return cls(role=Role.User, content=content)

    @classmethod
    def assistant(cls, content: str) -> "Message":
        return cls(role=Role.Assistant, content=content)

    @classmethod
    def system(cls, content: str) -> "Message":
        return cls(role=Role.System, content=content)

    @classmethod
    def ipython(cls, content: str) -> "Message":
        return cls(role=Role.IPython, content=content)

    @classmethod
    def from_tool_response(cls, tool_response: ToolResponse) -> "Message":
        """Construct a message from a tool response.

        This is a convenience method which allows a quick conversion of a tool response
        to the message.
        """
        return cls(role=Role.IPython, content=None, tool_response=tool_response)

    def render(self) -> str:
        if self.tool_call is not None:
            assert self.role == Role.Assistant, "Tool call must be an assistant message"
            return f"{self.role.header}\n\n{self.tool_call.render()}{SpecialTokens.EndOfMessage.value}"

        if self.tool_response is not None:
            assert self.role == Role.IPython, "Tool response must be an ipython message"
            return f"{self.role.header}\n\n{self.tool_response.render()}{SpecialTokens.EndOfTurn.value}"

        assert self.content is not None, "Content must be present"
        return f"{self.role.header}\n\n{self.content}{SpecialTokens.EndOfTurn.value}"


@dataclass
class ChatResponse:
    message: Message

    @classmethod
    def from_text(cls, raw: RawResponse) -> "ChatResponse":
        response = Response.from_raw(raw)
        tool_call = ToolCall.from_response(response)
        if tool_call is None:
            message = Message(role=Role.Assistant, content=response.text)
        else:
            message = Message(
                role=Role.Assistant,
                content=None,
                tool_call=tool_call,
            )
        return ChatResponse(message=message)
