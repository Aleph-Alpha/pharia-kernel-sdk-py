"""
A message represents one turn in a conversation with an LLM.

1. To start a conversation with an LLM, a developer creates a user and optionally system message: `UserMessage(content)`.
2. The LLM responds with an `AssistantReply` or a `ToolRequest`.
3. If the LLM has requested a tool call, the developer executes the tool call and responds with a `ToolResponse`.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Literal, Sequence

from .response import RawResponse, Response, SpecialTokens
from .tool import ToolDefinition
from .tool_call import ToolCall


class Role(str, Enum):
    """A role used for a message in a chat."""

    User = "user"
    Assistant = "assistant"
    System = "system"
    IPython = "ipython"

    def render(self) -> str:
        return f"<|start_header_id|>{self.value.lower()}<|end_header_id|>"


@dataclass
class UserMessage:
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
class SystemMessage:
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


@dataclass
class ToolMessage:
    """
    Response for the model after a tool call has been executed.

    Given the LLM has requested a tool call and the developer has executed the tool call,
    the result can be passed back to the model as a `ToolResponse`.
    """

    content: str
    role: Literal[Role.IPython] = Role.IPython
    success: bool = True

    def __init__(self, content: str, success: bool = True):
        self.content = content
        self.success = success

    def render(self) -> str:
        return f"{self.role.render()}\n\n{self.output()}{SpecialTokens.EndOfTurn.value}"

    def output(self) -> str:
        prompt = "completed" if self.success else "failed"
        if self.success:
            prompt += f"[stdout]{self.content}[/stdout]"
        else:
            prompt += f"[stderr]{self.content}[/stderr]"
        return prompt


@dataclass
class AssistantReply:
    """A "normal" (no tool call) response from the model."""

    content: str
    role: Literal[Role.Assistant] = Role.Assistant

    # keep the `tool_calls` field as it allows consumers to do:
    # `if response.message.tool_calls: ...` instead of needing to do a type check
    # like `if isinstance(response.message, ToolRequest): ...`
    tool_calls: None = None

    def __init__(self, content: str):
        self.content = content

    def render(self) -> str:
        return f"{self.role.render()}\n\n{self.content}{SpecialTokens.EndOfTurn.value}"


@dataclass
class AssistantToolRequest:
    """A response from the LLM that contains a tool call."""

    tool_calls: list[ToolCall]
    role: Literal[Role.Assistant] = Role.Assistant

    # keep the content field, see `AssistantReply` for explanation
    content: None = None

    def __init__(self, tool_calls: list[ToolCall]):
        self.tool_calls = tool_calls

    def render(self) -> str:
        """Llama will end messages with <|eom_id|> instead of <|eot_id|> if it responds
        with a tool call and `Environment: ipython` is set in the system prompt. If `ipython`
        is not turned on, it will also end tool calls with <|eot_id|>.

        Reference: https://www.llama.com/docs/model-cards-and-prompt-formats/llama3_1/

        We always turn on `ipython` in the system prompt, so we always use `<|eom_id|>` for serialization.
        """
        content = "".join([tool_call.render() for tool_call in self.tool_calls])
        return f"{self.role.render()}\n\n{content}{SpecialTokens.EndOfMessage.value}"


AssistantMessage = AssistantToolRequest | AssistantReply
"""A message that is returned from the LLM."""


def from_raw_response(
    raw: RawResponse, tools: Sequence[ToolDefinition] | None = None
) -> AssistantMessage:
    response = Response.from_raw(raw)
    if tools:
        tool_call = ToolCall.from_response(response)
        if tool_call is not None:
            tool_call.try_parse(tools)
            return AssistantToolRequest([tool_call])
    return AssistantReply(response.text)
