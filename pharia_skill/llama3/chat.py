"""Take a chat request and convert it to a prompt"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class StopReason(str, Enum):
    EndOfTurn = "<|eot_id|>"
    EndOfMessage = "<|eom_id|>"


class Role(str, Enum):
    """A role used for a message in a chat."""

    User = "user"
    Assistant = "assistant"
    System = "system"
    IPython = "ipython"

    @property
    def header(self) -> str:
        return f"<|start_header_id|>{self.value.lower()}<|end_header_id|>"


class BuiltInTool(str, Enum):
    CodeInterpreter = "code_interpreter"
    WolframAlpha = "wolfram_alpha"
    BraveSearch = "brave_search"


@dataclass
class ToolDefinition:
    tool_name: BuiltInTool


@dataclass
class ToolCall:
    tool_name: BuiltInTool | str
    arguments: dict[str, Any]


@dataclass
class Message:
    """Describes a message in a chat.

    Parameters:
        role (Role, required): The role of the message.
        content (str, required): The content of the message.
    """

    role: Role
    content: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)

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

    def as_prompt(self) -> str:
        return f"{self.role.header}\n\n{self.content}{StopReason.EndOfTurn.value}"


def validate_messages(messages: list[Message]) -> None:
    """Validate the order of messages in a chat request."""
    if not messages:
        raise ValueError("Messages cannot be empty")

    if messages[0].role not in (Role.System, Role.User):
        raise ValueError("First message must be a system or user message")

    cursor = 1 if messages[0].role == Role.System else 0

    # check that alternating between user/tool and assistant
    for i, message in enumerate(messages[cursor:]):
        if i % 2 == 0:
            if message.role not in (Role.User, Role.IPython):
                raise ValueError("User messages must alternate with assistant messages")
        else:
            if message.role != Role.Assistant:
                raise ValueError("Assistant messages must alternate with user messages")

    # check that the last message is a user/ipython message
    if messages[-1].role not in (Role.User, Role.IPython):
        raise ValueError("Last message must be a user or ipython message")


@dataclass
class ChatRequest:
    messages: list[Message]
    tools: list[ToolDefinition] = field(default_factory=list)

    def __post_init__(self) -> None:
        validate_messages(self.messages)

    def build_in_tools_without_code_interpreter(self) -> list[ToolDefinition]:
        return [
            tool for tool in self.tools if tool.tool_name != BuiltInTool.CodeInterpreter
        ]

    @property
    def system(self) -> Message | None:
        """Augment the system prompt with the tools"""
        if not self.tools:
            return self.messages[0] if self.messages[0].role == Role.System else None

        prompt = "Environment: ipython"
        if tools := self.build_in_tools_without_code_interpreter():
            prompt += f"\nTools: {', '.join(tool.tool_name for tool in tools)}"

        if self.messages[0].role == Role.System:
            prompt += f"\n{self.messages[0].content}"
        return Message.system(prompt)

    def messages_without_system(self) -> list[Message]:
        return [message for message in self.messages if message.role != Role.System]

    def as_prompt(self) -> str:
        """Convert the chat request to a prompt"""
        prompt = "<|begin_of_text|>"
        prompt += self.system.as_prompt() if self.system else ""

        for message in self.messages_without_system():
            prompt += message.as_prompt()

        prompt += Role.Assistant.header
        prompt += "\n\n"
        return prompt


@dataclass
class ChatResponse:
    message: Message

    @staticmethod
    def from_reply(reply: str) -> "ChatResponse":
        reply = reply.replace(StopReason.EndOfTurn, "")
        reply = reply.replace(StopReason.EndOfMessage, "")
        reply = reply.strip()
        if reply.startswith("<|python_tag|>"):
            stripped = reply[len("<|python_tag|>") :]
            if stripped.startswith("brave_search.call"):
                tool_call = ToolCall(
                    tool_name=BuiltInTool.BraveSearch,
                    arguments={
                        "query": stripped.split('brave_search.call(query="')[1]
                        .split('")')[0]
                        .strip()
                    },
                )
            elif stripped.startswith("wolfram_alpha.call"):
                tool_call = ToolCall(
                    tool_name=BuiltInTool.WolframAlpha,
                    arguments={
                        "query": stripped.split('wolfram_alpha.call(query="')[1]
                        .split('")')[0]
                        .strip()
                    },
                )
            else:
                tool_call = ToolCall(
                    tool_name=BuiltInTool.CodeInterpreter,
                    arguments={"code": stripped.strip()},
                )
            message = Message(
                role=Role.Assistant,
                content=None,
                tool_calls=[tool_call],
            )
            return ChatResponse(message=message)
        return ChatResponse(message=Message.assistant(reply))
