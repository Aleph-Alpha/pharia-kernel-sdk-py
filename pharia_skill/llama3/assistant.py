from dataclasses import dataclass
from typing import Literal, Sequence

from .message import MessageApi, Role
from .response import RawResponse, Response, SpecialTokens
from .tool import ToolCall, ToolDefinition


@dataclass
class AssistantReply(MessageApi):
    """A "normal" (no tool call) response from the model."""

    content: str
    role: Literal[Role.Assistant] = Role.Assistant

    # keep the `tool_calls` field as it allows consumers to do:
    # `if response.message.tool_calls: ...` instead of needing to do a type check
    # like `if isinstance(response.message, ToolRequest): ...`
    tool_calls: None = None

    def render(self) -> str:
        return f"{self.role.render()}\n\n{self.content}{SpecialTokens.EndOfTurn.value}"


@dataclass
class ToolRequest(MessageApi):
    """A response from the LLM that contains a tool call."""

    tool_calls: list[ToolCall]
    role: Literal[Role.Assistant] = Role.Assistant

    # keep the content field, see `AssistantReply` for explanation
    content: None = None

    def render(self) -> str:
        """Llama will end messages with <|eom_id|> instead of <|eot_id|> if it responds
        with a tool call and `Environment: ipython` is set in the system prompt. If `ipython`
        is not turned on, it will also end tool calls with <|eot_id|>.

        Reference: https://www.llama.com/docs/model-cards-and-prompt-formats/llama3_1/

        We always turn on `ipython` in the system prompt, so we always use `<|eom_id|>` for serialization.
        """
        content = "".join([tool_call.render() for tool_call in self.tool_calls])
        return f"{self.role.render()}\n\n{content}{SpecialTokens.EndOfMessage.value}"


AssistantMessage = ToolRequest | AssistantReply
"""A message that is returned from the LLM."""


def from_raw_response(
    raw: RawResponse, tools: Sequence[ToolDefinition] | None = None
) -> AssistantMessage:
    response = Response.from_raw(raw)
    if tools:
        tool_call = ToolCall.from_response(response)
        if tool_call is not None:
            tool_call.try_parse(tools)
            return ToolRequest(content=None, tool_calls=[tool_call])
    return AssistantReply(content=response.text)
