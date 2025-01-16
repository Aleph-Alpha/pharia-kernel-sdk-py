from dataclasses import dataclass
from typing import Literal, Sequence

from .message import MessageApi, Role
from .response import RawResponse, Response, SpecialTokens
from .tool import ToolCall, ToolDefinition


@dataclass
class AssistantMessage(MessageApi):
    """A message that is returned from the LLM.

    With tool calling, the different messages diverge in their attributes,
    which is why they are represented by different classes.
    """

    content: str | None = None
    role: Literal[Role.Assistant] = Role.Assistant
    tool_call: ToolCall | None = None

    @classmethod
    def from_raw_response(
        cls, raw: RawResponse, tools: Sequence[ToolDefinition] | None = None
    ) -> "AssistantMessage":
        response = Response.from_raw(raw)
        if tools:
            tool_call = ToolCall.from_response(response)
            if tool_call is not None:
                tool_call.try_parse(tools)
                return AssistantMessage(tool_call=tool_call)
        return AssistantMessage(content=response.text)

    def render(self) -> str:
        """Llama will end messages with <|eom_id|> instead of <|eot_id|> if it responds
        with a tool call and `Environment: ipython` is set in the system prompt. If `ipython`
        is not turned on, it will also end tool calls with <|eot_id|>.

        Reference: https://www.llama.com/docs/model-cards-and-prompt-formats/llama3_1/

        We always turn on `ipython` in the system prompt, so we always use `<|eom_id|>` for serialization.
        """
        if self.tool_call is not None:
            return f"{self.role.render()}\n\n{self.tool_call.render()}{SpecialTokens.EndOfMessage.value}"

        return f"{self.role.render()}\n\n{self.content}{SpecialTokens.EndOfTurn.value}"
