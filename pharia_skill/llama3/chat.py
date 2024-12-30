"""Take a chat request and convert it to a prompt"""

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel


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
    """A tool can either be a built-in tool or a custom tool."""

    tool_name: BuiltInTool | str
    description: str | None = None

    # the user can define parameters with a custom pydantic model
    parameters: type[BaseModel] | None = None

    def as_dict(self) -> dict[str, Any]:
        prompt = {
            "type": "function",
            "function": {
                "name": self.tool_name,
                "description": self.description,
                "parameters": self.parameters.model_json_schema()
                if self.parameters is not None
                else None,
            },
        }
        return prompt

    def as_prompt(self) -> str:
        return json.dumps(self.as_dict(), indent=4)


@dataclass
class ToolResponse:
    tool_name: BuiltInTool
    status: Literal["success", "failure"]
    # can be a any str representation of the output, e.g. '{"result": "[]"}'
    stdout: str | None
    stderr: str | None

    def as_prompt(self) -> str:
        prompt = "completed" if self.status == "success" else "failed"
        if self.stdout:
            prompt += f"[stdout]{self.stdout}[/stdout]"
        if self.stderr:
            prompt += f"[stderr]{self.stderr}[/stderr]"
        return prompt


@dataclass
class ToolCall:
    tool_name: BuiltInTool
    arguments: dict[str, str]

    def as_prompt(self) -> str:
        """Reconstruct the model response from a parsed tool call.

        There should only be one source of truth. As the response is stored in
        a parsed format, we need to convert it to a prompt string to construct
        the message history for a later interactions with the model.
        """
        if self.tool_name == BuiltInTool.CodeInterpreter:
            assert "code" in self.arguments
            return self.arguments["code"]
        elif self.tool_name == BuiltInTool.BraveSearch:
            assert "query" in self.arguments
            return f'brave_search.call(query="{self.arguments["query"]}")'
        elif self.tool_name == BuiltInTool.WolframAlpha:
            assert "query" in self.arguments
            return f'wolfram_alpha.call(query="{self.arguments["query"]}")'
        raise ValueError(f"Unsupported tool name: {self.tool_name}")


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

    def as_prompt(self) -> str:
        if self.tool_call is not None:
            assert self.role == Role.Assistant, "Tool call must be an assistant message"
            return f"{self.role.header}\n\n<|python_tag|>{self.tool_call.as_prompt()}{StopReason.EndOfMessage.value}"

        if self.tool_response is not None:
            assert self.role == Role.IPython, "Tool response must be an ipython message"
            return f"{self.role.header}\n\n{self.tool_response.as_prompt()}{StopReason.EndOfTurn.value}"

        assert self.content is not None, "Content must be present"
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
            tool
            for tool in self.tools
            if tool.tool_name in list(BuiltInTool)
            and tool.tool_name != BuiltInTool.CodeInterpreter
        ]

    def user_provided_tools(self) -> list[ToolDefinition]:
        return [tool for tool in self.tools if tool.tool_name not in list(BuiltInTool)]

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

    @property
    def user(self) -> Message:
        provided = (
            self.messages[0] if self.messages[0].role == Role.User else self.messages[1]
        )
        assert provided.role == Role.User, "User message must be provided"

        if not self.user_provided_tools():
            return provided

        prompt = "Answer the user's question by making use of the following functions if needed.\n\n"
        for tool in self.user_provided_tools():
            prompt += f"{tool.as_prompt()}\n"

        prompt += "\nReturn function calls in JSON format."
        prompt += f"\n\nQuestion: {provided.content}"
        return Message.user(prompt)

    def messages_without_system_and_first_user(self) -> list[Message]:
        messages = [message for message in self.messages if message.role != Role.System]
        return messages[1:]

    def as_prompt(self) -> str:
        """Convert the chat request to a prompt"""
        prompt = "<|begin_of_text|>"
        prompt += self.system.as_prompt() if self.system else ""
        prompt += self.user.as_prompt()

        for message in self.messages_without_system_and_first_user():
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
                tool_call=tool_call,
            )
            return ChatResponse(message=message)
        return ChatResponse(message=Message.assistant(reply))
