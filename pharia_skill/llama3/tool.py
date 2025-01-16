"""
Tools integrate LLMs with external services.

For this, three points of interactions are needed, which are represented by three
classes in this module.

1. The model needs to know a about the available tools (`ToolDefinition`).
2. The model needs to be able to call a tool (`ToolCall`).
3. The model needs to know th result of the tool call (`ToolResponse`).
"""

import json
import re
from dataclasses import dataclass
from typing import Any, Literal, Sequence

from pydantic import BaseModel

# import from typing_extensions for Python < 3.12 compatibility
from typing_extensions import TypedDict

from .message import MessageApi, Role
from .response import Response, SpecialTokens


@dataclass
class ToolResponse(MessageApi):
    """
    Response for the model after a tool call has been executed.

    Given the LLM has requested a tool call and the developer has executed the tool call,
    the result can be passed back to the model as a `ToolResponse`.
    """

    content: str
    role: Literal[Role.IPython] = Role.IPython
    success: bool = True

    def render(self) -> str:
        return f"{self.role.render()}\n\n{self.output()}{SpecialTokens.EndOfTurn.value}"

    def output(self) -> str:
        prompt = "completed" if self.success else "failed"
        if self.success:
            prompt += f"[stdout]{self.content}[/stdout]"
        else:
            prompt += f"[stderr]{self.content}[/stderr]"
        return prompt


class Function(TypedDict):
    name: str
    description: str | None
    parameters: dict[str, Any]


class JsonSchema(TypedDict):
    """Provide a tool definition as a json schema.

    While `Tool` is a more user-friendly way to define a tool in
    code, in some cases it might put too many constraints on the user. E.g., it can
    not be serialized from a json http request. Therefore, function definitions can
    also be provided in the serialized, json schema format.
    """

    type: Literal["function"]
    function: Function


class Tool(BaseModel):
    """Provide a tool definition as a Pydantic model.

    The name of the class will be used as function name. The description of the
    function is taken from the docstring of the class. The parameters are
    specified as attributes of the model. Type hints and default arguments can
    be used to specify the schema, and a description of a parameter can be added
    with the `Field` class.

    Example::

        from pydantic import BaseMode, Field

        class GetImageInformation(BaseModel):
            "Retrieve information about a specific image."

            registry: str
            repository: str = Field(
                description="The full identifier of the image in the registry",
            )
            tag: str = "latest"
    """

    @classmethod
    def json_schema(cls) -> dict[str, Any]:
        """The (slightly incompliant) json schema of a tool.

        For all specified tools, this schema is passed to the model.
        LLama expects a json object with `type` "function" as the root elements
        and a `function` object with the keys `name`, `description`, and `parameters`.

        Only for the parameters, we can make use of the json schema representation of a
        pydantic models. Note that the output schema is invalid json schema, as there is
        no `function` type in the json schema specification:

        https://json-schema.org/draft/2020-12/json-schema-validation#section-6.1.1
        """
        schema = cls.model_json_schema()
        description = schema.get("description")
        if description is not None:
            del schema["description"]
        data = {
            "type": "function",
            "function": {
                "name": cls.name(),
                "description": description,
                "parameters": schema,
            },
        }
        cls._recursive_purge_title(data)
        return data

    @classmethod
    def name(cls) -> str:
        return cls._to_snake_case(cls.__name__)

    @classmethod
    def _to_snake_case(cls, name: str) -> str:
        return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()

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

    def render_tool_call(self) -> str:
        """Convert a tool call to prompt format again.

        When a tool call has been loaded from a model response, it is part of the
        conversation and needs to be converted back to a prompt when providing the
        full conversation history to the model for the next turn.
        """
        return json.dumps(
            {
                "type": "function",
                "name": self.name(),
                "parameters": self.model_dump(exclude_unset=True),
            }
        )


class CodeInterpreter(Tool):
    src: str

    def render_tool_call(self) -> str:
        return SpecialTokens.PythonTag + self.src

    def run(self) -> ToolResponse:
        global_vars: dict[str, Any] = {}
        exec(self.src, global_vars)
        return ToolResponse(content=str(global_vars.get("result")))


class WolframAlpha(Tool):
    query: str

    def render_tool_call(self) -> str:
        return SpecialTokens.PythonTag + f'wolfram_alpha.call(query="{self.query}")'


class BraveSearch(Tool):
    query: str

    def render_tool_call(self) -> str:
        return SpecialTokens.PythonTag + f'brave_search.call(query="{self.query}")'


BuiltInTools: tuple[type[Tool], ...] = (CodeInterpreter, WolframAlpha, BraveSearch)


ToolDefinition = type[Tool] | JsonSchema
"""A tool can either be defined as a Pydantic model or directly as a json schema."""


@dataclass
class ToolCall:
    """A tool call as parsed from the response of the model.

    Arguments are not validated against the provided schema.
    """

    name: str
    arguments: Tool | dict[str, Any]

    def render(self) -> str:
        """Reconstruct the model response from a parsed tool call.

        There should only be one source of truth. As the response is stored in
        a parsed format, we need to convert it to a prompt string to construct
        the message history for a later interactions with the model.
        """
        if isinstance(self.arguments, dict):
            return json.dumps(
                {"type": "function", "name": self.name, "parameters": self.arguments}
            )
        return self.arguments.render_tool_call()

    def try_parse(self, tools: Sequence[ToolDefinition]) -> None:
        """Try to validate a tool call into one of the provided tools.

        This provides the user with strong type hints.
        """
        arguments = self.arguments
        if not isinstance(arguments, dict):
            # already parsed
            return

        for tool in tools:
            if isinstance(tool, type) and tool.name() == self.name:
                self.arguments = tool(**arguments)

    @classmethod
    def from_response(cls, text: Response) -> "ToolCall | None":
        """Parse a tool call from a message that has been stripped of special tokens.

        While llama3.1 always includes the <|python_tag|> prefix for function calls,
        llama3.3 does not. Therefore, we always try to match a function call from the response,
        even if the python tag is not included. Built in tools are always prefixed with the
        python tag, even by llama3.3.

        This contradicts https://github.com/meta-llama/llama-models/blob/main/models/llama3_3/prompt_format.md#model-response-format-5

        Args:
            text (str): The text of the message stripped of any special tokens.
            python_tag (bool): Whether the message started with the Python Tag.
        """

        if text.python_tag:
            return cls.json_from_text(text.text) or cls.built_in_from_text(text.text)
        else:
            return cls.json_from_text(text.text)

    @staticmethod
    def built_in_from_text(text: str) -> "ToolCall":
        """Parse a tool call from a message that started with the Python Tag."""
        if text.startswith("brave_search.call"):
            return ToolCall(
                "brave_search",
                BraveSearch(
                    query=text.split('brave_search.call(query="')[1]
                    .split('")')[0]
                    .strip()
                ),
            )
        elif text.startswith("wolfram_alpha.call"):
            return ToolCall(
                "wolfram_alpha",
                WolframAlpha(
                    query=text.split('wolfram_alpha.call(query="')[1]
                    .split('")')[0]
                    .strip()
                ),
            )
        else:
            return ToolCall(
                "code_interpreter",
                CodeInterpreter(src=text.strip()),
            )

    @staticmethod
    def json_from_text(response: str) -> "ToolCall | None":
        try:
            data = json.loads(response)
            name = data["name"]
            return ToolCall(name, data["parameters"])
        except (json.JSONDecodeError, KeyError):
            pass

        return None
