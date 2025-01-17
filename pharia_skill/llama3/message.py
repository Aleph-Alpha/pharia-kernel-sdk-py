"""
A message represents one turn in a conversation with an LLM.

1. To start a conversation with an LLM, a developer creates a user and optionally system message: `UserMessage(content)`.
2. The LLM responds with an `AssistantReply` or a `ToolRequest`.
3. If the LLM has requested a tool call, the developer executes the tool call and responds with a `ToolResponse`.
"""

import json
from dataclasses import dataclass
from enum import Enum
from typing import Literal, Sequence

from .response import RawResponse, Response, SpecialTokens
from .tool import BuiltInTools, CodeInterpreter, Tool, ToolDefinition
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

    def render(self, tools: Sequence[ToolDefinition]) -> str:
        def render_tool(tool: ToolDefinition) -> str:
            schema = tool if isinstance(tool, dict) else tool.json_schema()
            return json.dumps(schema, indent=4)

        def render_content(content: str) -> str:
            return f"{Role.User.render()}\n\n{content}{SpecialTokens.EndOfTurn.value}"

        if not (tools := self.json_based_tools(tools)):
            return render_content(self.content)

        prompt = "Answer the user's question by making use of the following functions if needed.\n\n"
        for tool in tools:
            prompt += f"{render_tool(tool)}\n"

        prompt += "\nReturn function calls in JSON format."
        prompt += f"\n\nQuestion: {self.content}"
        return render_content(prompt)

    @staticmethod
    def json_based_tools(tools: Sequence[ToolDefinition]) -> Sequence[ToolDefinition]:
        """Tools that are defined as JSON schema and invoked with json based tool calling.

        We insert these in the user prompt. The model card states:

        The tool definition is provided in the user prompt, as that is how the model was
        trained for the built in JSON tool calling. However, it's possible to provide
        the tool definition in the system prompt as well—and get similar results.
        Developers must test which way works best for their use case.
        """
        return [tool for tool in tools if tool not in BuiltInTools]


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

    @classmethod
    def empty(cls) -> "SystemMessage":
        """Create an empty system message.

        When the user has not provided a system message but specified tools, we create
        an empty system message that can be rendered with the tools.
        """
        return cls("")

    def render(self, tools: Sequence[ToolDefinition]) -> str:
        """Render a system message and inject tools into the prompt.

        Conditionally activate the IPython environment if any tools are provided. Activating
        this environment is optional in case there is only user-defined tools. By always activating
        it, we don't need to parse this knowledge to `AssistantMessage.render`, and can always end
        in <|eom_id|> token.

        If built in tools are configured, they are listed in the system prompt.
        The code interpreter tools is automatically included when IPython is activated.

        Reference: https://github.com/meta-llama/llama-models/blob/main/models/llama3_3/prompt_format.md#input-prompt-format-2
        """

        def render_content(content: str) -> str:
            return f"{Role.System.render()}\n\n{content}{SpecialTokens.EndOfTurn.value}"

        if not tools:
            return render_content(self.content)

        content = "Environment: ipython"
        if filtered := self.system_prompt_tools(tools):
            content += f"\nTools: {', '.join(tool.name() for tool in filtered)}"

        if CodeInterpreter in tools:
            content += "\nIf you decide to run python code, assign the result to a variable called `result`."

        # include the original system prompt
        if self.content:
            content += f"\n{self.content}"
        return render_content(content)

    @staticmethod
    def system_prompt_tools(tools: Sequence[ToolDefinition]) -> list[type[Tool]]:
        """Subset of specified tools that need to be activated in the system prompt.

        CodeInterpreter is automatically included when IPython is activated and does
        not need to be listed in the system prompt.
        """
        return [
            tool
            for tool in tools
            if isinstance(tool, type)
            and tool in BuiltInTools
            and not tool == CodeInterpreter
        ]


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

    def render(self, tools: Sequence[ToolDefinition]) -> str:
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

    def render(self, tools: Sequence[ToolDefinition]) -> str:
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

    def render(self, tools: Sequence[ToolDefinition]) -> str:
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
