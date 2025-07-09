import datetime as dt
import json
from typing import Iterator, Literal

from pydantic import BaseModel, RootModel, ValidationError
from pydantic.dataclasses import dataclass
from pydantic.types import JsonValue

from .types import ChatEvent, Message, MessageAppend, Role


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
    if messages[0].role == Role.System:
        system = _render_system(today, tools, messages[0].content)
        return [Message.system(system)] + messages[1:]
    else:
        system = _render_system(today, tools, "")
        return [Message.system(system)] + messages


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

    def _render(self) -> str:
        """Render the tool output to the format received by the model."""
        return f'completed[stdout]:{{"result": {self.text()}}}[/stdout]'

    def as_message(self) -> Message:
        """Render the tool output to a message."""
        return Message.tool(self._render())


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


@dataclass(frozen=True)
class ToolCallRequest:
    """A request from a model to invoke a tool."""

    name: str
    parameters: dict[str, JsonValue]

    def _render(self) -> str:
        """Render the tool call to the format received by the model.

        This is necessary to add a tool call to the message history again.
        """
        return "<|python_tag|>" + json.dumps(
            {
                "type": "function",
                "function": {"name": self.name, "parameters": self.parameters},
            }
        )

    def as_message(self) -> Message:
        """Render the tool call to a message."""
        return Message.assistant(self._render())


def parse_tool_call(stream: Iterator[ChatEvent]) -> ToolCallRequest | None:
    """Inspect if a stream contains a tool call with minimal polls.

    If the stream does not contain a tool call, return `None` as soon as possible,
    so the caller can still stream the response.

    Currently, as our inference API does not have a tool call concept in their events,
    we need to do this in the SDK. For streaming, this is an interesting problem, as
    a decision on whether a chunk is part of a normal message or part of a tool call
    needs to be taken on the fly. This is what this function does.
    """
    # Possible start sequences for a tool call. The might be split over multiple chunks.
    start_sequences = ("```json\n{", "```{", "{")
    maybe_tool_call: str = ""

    for event in stream:
        if not isinstance(event, MessageAppend):
            continue

        # Empty chunk can occur before a tool call.
        if event.content == "":
            continue

        maybe_tool_call += event.content
        if not could_be_tool_call(maybe_tool_call, start_sequences):
            # We can return early here. There is no tool call.
            return None

    if maybe_tool_call:
        try:
            return _deserialize_tool_call(maybe_tool_call)
        except ValidationError:
            pass

    return None


def could_be_tool_call(content: str, start_sequences: tuple[str, ...]) -> bool:
    """Check if the content string could start with any of the start sequences.

    Note that it does not need to fully start with the start sequence, but it is just
    about if it could still start with one of the start sequences if more chunks
    come in.
    """
    for sequence in start_sequences:
        # There are two possible cases:
        # 1. Content starts with sequence.
        #     content = "```json\n{"function"
        #     sequence = "```json\n{"
        # 2. Sequence starts with content:
        #     content = "``"
        #     sequence = "```json\n{"
        if content.startswith(sequence) or sequence.startswith(content):
            return True
    return False


def _deserialize_tool_call(content: str) -> ToolCallRequest:
    """Deserialize a tool call from a plain text response.

    Notably, `llama-3.3-70b-instruct` returns different formats for tool calls.
    We try to support all formats.
    """

    class Function(BaseModel):
        name: str
        parameters: dict[str, JsonValue]

    class StandardFormat(BaseModel):
        type: Literal["function"]
        function: Function

    class OtherFormat(BaseModel):
        type: Literal["function"]
        name: str
        parameters: dict[str, JsonValue]

    Deserializer = RootModel[StandardFormat | OtherFormat]

    content = _remove_md_delimiters(content)

    match Deserializer.model_validate_json(content).root:
        case StandardFormat(function=function):
            return ToolCallRequest(name=function.name, parameters=function.parameters)
        case OtherFormat(name=name, parameters=parameters):
            return ToolCallRequest(name=name, parameters=parameters)
        case _:
            raise ValueError("This will never happen.")


def _remove_md_delimiters(content: str) -> str:
    """Remove the ```json\n or ``` if present."""
    content = _remove_md_prefix(content)
    content = _remove_md_suffix(content)
    return content


def _remove_md_prefix(content: str) -> str:
    """Remove the ```json\n or ``` if present."""

    # The order matters here. Start with the longer prefix.
    to_remove = ("```json\n", "```")
    for prefix in to_remove:
        if content.startswith(prefix):
            return content[len(prefix) :]
    return content


def _remove_md_suffix(content: str) -> str:
    if content.endswith("```"):
        return content[:-3]
    return content
