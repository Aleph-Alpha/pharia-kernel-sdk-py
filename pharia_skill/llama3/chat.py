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

    name: BuiltInTool | str
    description: str | None = None

    # the user can define parameters with a custom pydantic model
    parameters: type[BaseModel] | None = None

    @classmethod
    def _recursive_purge_title(cls, data: dict[str, Any]) -> None:
        """Remove the title field from a dictionary recursively.

        The title is automatically created based on the name of the pydantic model,
        but it is not shown in examples of the llama model card, hence we skip it.
        See https://github.com/pydantic/pydantic/discussions/8504 for more detail.
        """
        if isinstance(data, dict):
            for key in list(data.keys()):
                if key == "title" and "type" in data.keys():
                    del data[key]
                else:
                    cls._recursive_purge_title(data[key])

    def as_dict(self) -> dict[str, Any]:
        if self.parameters:
            parameters = self.parameters.model_json_schema()
            self._recursive_purge_title(parameters)
        else:
            parameters = {}
        prompt = {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": parameters,
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
    tool_name: BuiltInTool | str
    arguments: dict[str, str]

    def as_json(self) -> str:
        return json.dumps(
            {"type": "function", "name": self.tool_name, "parameters": self.arguments}
        )

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
        else:
            return self.as_json()


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

    def built_in_tools_without_code_interpreter(self) -> list[ToolDefinition]:
        return [
            tool
            for tool in self.tools
            if tool.name in list(BuiltInTool)
            and tool.name != BuiltInTool.CodeInterpreter
        ]

    def user_provided_tools(self) -> list[ToolDefinition]:
        return [tool for tool in self.tools if tool.name not in list(BuiltInTool)]

    @property
    def system(self) -> Message | None:
        """Augment the system prompt with the tools"""
        if not self.tools:
            return self.messages[0] if self.messages[0].role == Role.System else None

        prompt = "Environment: ipython"
        if tools := self.built_in_tools_without_code_interpreter():
            prompt += f"\nTools: {', '.join(tool.name for tool in tools)}"

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
    def json_tool_call(response: str) -> ToolCall | None:
        try:
            data = json.loads(response)
            name = data["name"]
            return ToolCall(name, data["parameters"])
        except (json.JSONDecodeError, KeyError):
            pass

        return None

    @staticmethod
    def built_in_tool_call(response: str) -> ToolCall:
        """Parse a tool call from a message that started with the Python Tag."""
        if response.startswith("brave_search.call"):
            return ToolCall(
                tool_name=BuiltInTool.BraveSearch,
                arguments={
                    "query": response.split('brave_search.call(query="')[1]
                    .split('")')[0]
                    .strip()
                },
            )
        elif response.startswith("wolfram_alpha.call"):
            return ToolCall(
                tool_name=BuiltInTool.WolframAlpha,
                arguments={
                    "query": response.split('wolfram_alpha.call(query="')[1]
                    .split('")')[0]
                    .strip()
                },
            )
        else:
            return ToolCall(
                tool_name=BuiltInTool.CodeInterpreter,
                arguments={"code": response.strip()},
            )

    @classmethod
    def from_reply(cls, reply: str) -> "ChatResponse":
        reply = reply.replace(StopReason.EndOfTurn, "")
        reply = reply.replace(StopReason.EndOfMessage, "")
        reply = reply.strip()
        if not reply.startswith("<|python_tag|>"):
            return ChatResponse(message=Message.assistant(reply))

        stripped = reply[len("<|python_tag|>") :]
        tool_call = cls.json_tool_call(stripped) or cls.built_in_tool_call(stripped)

        message = Message(
            role=Role.Assistant,
            content=None,
            tool_call=tool_call,
        )
        return ChatResponse(message=message)
