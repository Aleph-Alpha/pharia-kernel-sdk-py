"""
A message is one turn in a conversation with an LLM. Messages are constructed in three ways:

1. To start a conversation with an LLM, a developer creates a user and optionally system message: `Message.user(content)`.
2. When the LLM responds, the raw response is parsed into a message: `Message.from_raw_response(raw_response)`.
3. Given the LLM has requested a tool call and the developer has executed the tool call, a message needs
to be constructed from the tool response: `Message.from_tool_response(tool_response)`.
"""

from dataclasses import dataclass
from enum import Enum

from .response import SpecialTokens
from .tool import ToolResponse


class Role(str, Enum):
    """A role used for a message in a chat."""

    User = "user"
    Assistant = "assistant"
    System = "system"
    IPython = "ipython"

    def render(self) -> str:
        return f"<|start_header_id|>{self.value.lower()}<|end_header_id|>"


@dataclass
class Message:
    """Describes a message in a chat.

    Parameters:
        role (Role, required): The role of the message.
        content (str, required): The content of the message.
    """

    role: Role
    content: str | None = None
    tool_response: ToolResponse | None = None

    @classmethod
    def user(cls, content: str) -> "Message":
        return cls(role=Role.User, content=content)

    @classmethod
    def system(cls, content: str) -> "Message":
        return cls(role=Role.System, content=content)

    @classmethod
    def from_tool_response(cls, tool_response: ToolResponse) -> "Message":
        """Construct a message from a tool response.

        Given the LLM has requested a tool call and you have executed the tool call,
        use this method to construct a message to append to the conversation.
        """
        return cls(role=Role.IPython, content=None, tool_response=tool_response)

    def render(self) -> str:
        if self.tool_response is not None:
            assert self.role == Role.IPython, "Tool response must be an ipython message"
            return f"{self.role.render()}\n\n{self.tool_response.render()}{SpecialTokens.EndOfTurn.value}"

        assert self.content is not None, "Content must be present"
        return f"{self.role.render()}\n\n{self.content}{SpecialTokens.EndOfTurn.value}"
