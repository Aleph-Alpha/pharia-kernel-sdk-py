"""
A message represents one turn in a conversation with an LLM.

1. To start a conversation with an LLM, a developer creates a user and optionally system message: `UserMessage(content)`.
2. The LLM responds with an `AssistantMessage` which can include tool calls.
3. If the LLM has requested a tool call, the developer executes the tool call and responds with a `ToolResponse`.
"""

import datetime as dt
import json
from dataclasses import dataclass
from enum import Enum
from typing import Literal, Sequence

from .response import RawResponse, Response, SpecialTokens
from .tool import BuiltInTools, CodeInterpreter, JsonSchema, Tool, ToolDefinition
from .tool_call import ToolCall


class Role(str, Enum):
    """A role used for a message in a chat."""

    User = "user"
    Assistant = "assistant"
    System = "system"
    IPython = "ipython"

    def render(self) -> str:
        return f"{SpecialTokens.StartHeader.value}{self.value.lower()}{SpecialTokens.EndHeader.value}"


@dataclass
class UserMessage:
    """Describes a user message in a chat.

    Parameters:
        content (str, required): The content of the message.
    """

    content: str
    role: Literal[Role.User] = Role.User

    def render(self, tools: Sequence[ToolDefinition]) -> str:
        return f"{Role.User.render()}\n\n{self.content}{SpecialTokens.EndOfTurn.value}"

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

    This class is not exposed to the user and is not part of the conversation history like other messages.
    Instead, there is an optional `system` field on the `ChatRequest` which the user can use to set the system message.
    For rendering of the chat history, we then create a `SystemMessage` with the content of the `system` field.

    Parameters:
        content (str, required): The content of the message.
    """

    content: str
    role: Literal[Role.System] = Role.System

    def __init__(self, content: str):
        self.content = content

    def render(self, tools: Sequence[ToolDefinition]) -> str:
        """Render a system message and inject tools into the prompt.

        Always activate the IPython environment if any tools are provided. Activating
        this environment is optional in case there is only user-defined tools. However,
        eval shows that the tool call quality for json based tools is better when the
        IPython environment is activated.

        If built in tools are configured, they are listed in the system prompt.
        The code interpreter tools is automatically included when IPython is activated.

        Reference: https://github.com/meta-llama/llama-models/blob/main/models/llama3_3/prompt_format.md#input-prompt-format-2
        """

        def render_content(content: str) -> str:
            return f"{Role.System.render()}\n\n{content}{SpecialTokens.EndOfTurn.value}"

        def render_tool(tool: ToolDefinition) -> str:
            schema = (
                tool.model_dump()
                if isinstance(tool, JsonSchema)
                else tool.json_schema()
            )
            return json.dumps(schema, indent=4)

        if not tools:
            return render_content(self.content)

        # CodeInterpreter is automatically ijncluded when IPython is activated and does not need to be listed in the system prompt.
        content = "Environment: ipython"
        if filtered := self.system_prompt_tools(tools):
            content += f"\nTools: {', '.join(tool.name() for tool in filtered)}"

        if CodeInterpreter in tools:
            content += "\nIf you decide to run python code, assign the result to a variable called `result`."

        content += f"\nCutting Knowledge Date: December 2023\nToday Date: {dt.datetime.now().strftime('%d %B %Y')}"

        if json_tools := self.json_based_tools(tools):
            content += (
                "\n\nAnswer the user's question by making use of the following functions if needed.\n"
                "Only use functions if they are relevant to the user's question.\n"
                "Here is a list of functions in JSON format:\n"
            )
            for tool in json_tools:
                content += f"{render_tool(tool)}\n"
            content += "\nReturn function calls in JSON format."

        content += "\n\nYou are a helpful assistant."

        # include the original system prompt
        if self.content:
            content += f"\n{self.content}"
        return render_content(content)

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
            and tool != CodeInterpreter
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
        """Render the output of the tool call.

        The format defined for llama 3.0 seems to work well: https://github.com/meta-llama/llama-models/blob/main/models/llama3/prompt_templates/tool_response.py#L7

        The model card for 3.1 defines a different format `{"output": "..."}` (https://www.llama.com/docs/model-cards-and-prompt-formats/llama3_1/).
        However, this format does not produce good results.
        """
        prompt = "completed" if self.success else "failed"
        if self.success:
            prompt += f"[stdout]{self.content}[/stdout]"
        else:
            prompt += f"[stderr]{self.content}[/stderr]"
        return prompt


@dataclass
class AssistantMessage:
    """A message that is returned from the LLM."""

    content: str | None = None
    role: Literal[Role.Assistant] = Role.Assistant
    tool_calls: list[ToolCall] | None = None

    def render(self, tools: Sequence[ToolDefinition]) -> str:
        """Always end in <|eom_id|> for tool calls because we always activate the IPython environment.

        Llama will end messages with <|eom_id|> instead of <|eot_id|> if it responds
        with a tool call and `Environment: ipython` is set in the system prompt. If `ipython`
        is not turned on, it will also end tool calls with <|eot_id|>.

        Reference: https://www.llama.com/docs/model-cards-and-prompt-formats/llama3_1/
        """

        def render_content(
            content: str,
            end: Literal[SpecialTokens.EndOfTurn, SpecialTokens.EndOfMessage],
        ) -> str:
            return f"{Role.Assistant.render()}\n\n{content}{end.value}"

        if not self.tool_calls:
            assert self.content is not None, "Content must be set if no tool calls."
            return render_content(self.content, SpecialTokens.EndOfTurn)

        content = SpecialTokens.PythonTag.value
        content += "".join([tool_call.render() for tool_call in self.tool_calls])

        return render_content(content, SpecialTokens.EndOfMessage)

    @staticmethod
    def from_raw_response(
        raw: RawResponse, tools: Sequence[ToolDefinition] | None = None
    ) -> "AssistantMessage":
        response = Response.from_raw(raw)
        if tools and (tool_call := ToolCall.from_response(response, tools)):
            return AssistantMessage(tool_calls=[tool_call])
        return AssistantMessage(content=response.text)
