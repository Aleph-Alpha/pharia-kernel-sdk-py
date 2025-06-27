import datetime as dt
import json

from pydantic.dataclasses import dataclass
from pydantic.types import JsonValue

from pharia_skill.csi.inference import Message, Role


@dataclass
class InvokeRequest:
    name: str
    arguments: dict[str, JsonValue]


@dataclass
class Tool:
    name: str
    description: str
    input_schema: dict[str, JsonValue]

    def _json_schema(self) -> dict[str, JsonValue]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema,
            },
        }


def add_tools_to_system_prompt(
    messages: list[Message], tools: list[Tool]
) -> list[Message]:
    """Make a model aware about tools it can use.

    This function raises the level of abstraction on which developers think about
    talking to a model. Instead of needing to format the tools in the prompt, they
    pass them in, and this function takes care of rendering them as part of the system
    prompt. This abstraction is also what OpenAI compatible inference APIs provide.
    As long as we do not have support for that in the Kernel, we do this here.
    """
    if not tools:
        return messages

    today = dt.date.today()
    if messages[0].role != Role.System:
        system = _render_system(today, tools, "")
        messages.insert(0, Message.system(system))
    else:
        messages[0].content = _render_system(today, tools, messages[0].content)
    return messages


SYSTEM = """Environment: ipython
Cutting Knowledge Date: December 2023
Today Date: {today}

Answer the user's question by making use of the following functions if needed.
Only use functions if they are relevant to the user's question.
Here is a list of functions in JSON format:
{json_schema}

Return function calls in JSON format.

{existing_system}"""


def _render_system(today: dt.date, tools: list[Tool], existing_system: str) -> str:
    return SYSTEM.format(
        today=today.strftime("%d %B %Y"),
        json_schema="\n".join([json.dumps(t._json_schema(), indent=4) for t in tools]),
        existing_system=existing_system,
    )


@dataclass
class ToolOutput:
    """The output of a tool invocation.

    A tool result is a list of modalities.
    See <https://modelcontextprotocol.io/specification/2025-03-26/server/tools#tool-result>.
    At the moment, the Kernel only supports text modalities.

    Most tools will return a content list of size 1.
    """

    contents: list[str]

    def text(self) -> str:
        """Append all text contents to a single string.

        While the MCP specification allows for multiple modalities, in most cases
        MCP tools will return a single text modality. This property allows accessing
        the text content of the tool output as a single string.
        """
        return "\n\n".join(self.contents)


@dataclass
class ToolError(Exception):
    """The error message in case the tool invocation failed.

    A tool error can have different causes. The tool might not have been found,
    the arguments to the tool might have been in the wrong format, there could have
    been an error while connecting to the tool, or there could have been an error
    executing the tool.
    """

    message: str


ToolResult = ToolOutput | ToolError
"""The result of a tool invocation.

For almost all functionality offered by the CSI, errors are handled by the Kernel
runtime. If the error seems non-recoverable, Skill execution is suspended and the error
never makes it to user code.

For tools, however, the error is passed to the Skill. The reason for this is that there
is a good chance a Skill can recover from this error. Think of a model doing a tool
call. It might have misspelled the tool name or the arguments to the tool. If it
receives the error message, it can try a second time. Even if there is an error in the
tool itself, the model may decided that it can solve the users problem without this
particular tool. Therefore, tool errors are passed to the Skill.

For single tool calls, we stick to the Pythonic way and raise the `ToolError` as an
Exception. However, this pattern would not work for multiple parallel tool calls,
where the other results are still relevant even if one tool call fails. Therefore,
we introduce a `ToolResult` type.
"""
