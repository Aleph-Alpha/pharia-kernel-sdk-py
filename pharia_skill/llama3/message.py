"""
A message is one turn in a conversation with an LLM. Messages are constructed in three ways:

1. To start a conversation with an LLM, a developer creates a user and optionally system message: `Message.user(content)`.
2. The LLM responds with an `AssistantMessage` that may contain a tool call.
3. If the LLM has requested a tool call, the developer executes the tool call and responds with a `ToolResponse`.
"""

from dataclasses import dataclass
from enum import Enum

from .response import SpecialTokens


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
    """Describes a (user or system) message in a chat.

    Parameters:
        role (Role, required): The role of the message.
        content (str, required): The content of the message.
    """

    content: str | None
    role: Role

    @classmethod
    def user(cls, content: str) -> "Message":
        return cls(role=Role.User, content=content)

    @classmethod
    def system(cls, content: str) -> "Message":
        return cls(role=Role.System, content=content)

    def render(self) -> str:
        return f"{self.role.render()}\n\n{self.content}{SpecialTokens.EndOfTurn.value}"
