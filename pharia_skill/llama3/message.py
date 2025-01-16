"""
A class implementing `MessageApi` represents ne turn in a conversation with an LLM.

1. To start a conversation with an LLM, a developer creates a user and optionally system message: `UserMessage(content)`.
2. The LLM responds with an `AssistantReply` or a `ToolRequest`.
3. If the LLM has requested a tool call, the developer executes the tool call and responds with a `ToolResponse`.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Literal, Protocol

from .response import SpecialTokens


class Role(str, Enum):
    """A role used for a message in a chat."""

    User = "user"
    Assistant = "assistant"
    System = "system"
    IPython = "ipython"

    def render(self) -> str:
        return f"<|start_header_id|>{self.value.lower()}<|end_header_id|>"


class MessageApi(Protocol):
    """A base message that can be rendered."""

    def render(self) -> str:
        """Render the message to a string."""
        ...


@dataclass
class UserMessage(MessageApi):
    """Describes a user message in a chat.

    Parameters:
        content (str, required): The content of the message.
    """

    content: str
    role: Literal[Role.User] = Role.User

    def __init__(self, content: str):
        self.content = content

    def render(self) -> str:
        return f"{self.role.render()}\n\n{self.content}{SpecialTokens.EndOfTurn.value}"


@dataclass
class SystemMessage(MessageApi):
    """Describes a system message in a chat.

    Parameters:
        content (str, required): The content of the message.
    """

    content: str
    role: Literal[Role.System] = Role.System

    def __init__(self, content: str):
        self.content = content

    def render(self) -> str:
        return f"{self.role.render()}\n\n{self.content}{SpecialTokens.EndOfTurn.value}"
