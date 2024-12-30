"""Take a chat request and convert it to a prompt"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Role(str, Enum):
    """A role used for a message in a chat."""

    User = "user"
    Assistant = "assistant"
    System = "system"
    IPython = "ipython"


class BuiltInTool(str, Enum):
    CodeInterpreter = "code_interpreter"


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
    content: str
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
        header = f"<|start_header_id|>{self.role.value.lower()}<|end_header_id|>"
        content = f"\n\n{self.content}<|eot_id|>"
        return header + content


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

    def __post_init__(self) -> None:
        validate_messages(self.messages)

    def header(self, role: Role) -> str:
        return f"<|start_header_id|>{role.value.lower()}<|end_header_id|>"

    def as_prompt(self) -> str:
        """Convert the chat request to a prompt"""
        prompt = "<|begin_of_text|>"
        for message in self.messages:
            prompt += message.as_prompt()

        prompt += self.header(Role.Assistant)
        prompt += "\n\n"
        return prompt


@dataclass
class ChatResponse:
    message: Message

    @staticmethod
    def from_reply(reply: str) -> "ChatResponse":
        reply = reply.replace("<|eot_id|>", "")
        reply = reply.replace("<|eom_id|>", "")
        if reply.startswith("<|python_tag|>"):
            tool_call = ToolCall(
                tool_name=BuiltInTool.CodeInterpreter,
                arguments={"code": reply[len("<|python_tag|>") :].strip()},
            )
            message = Message(
                role=Role.Assistant,
                content="",
                tool_calls=[tool_call],
            )
            return ChatResponse(message=message)
        return ChatResponse(message=Message.assistant(reply))
