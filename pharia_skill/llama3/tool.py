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
from enum import Enum
from typing import Any, Literal, TypedDict

from pydantic import BaseModel

from .response import Response, SpecialTokens


class BuiltInTool(str, Enum):
    CodeInterpreter = "code_interpreter"
    WolframAlpha = "wolfram_alpha"
    BraveSearch = "brave_search"


class Function(TypedDict):
    name: str
    description: str
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
    def name(cls) -> str:
        return cls._to_snake_case(cls.__name__)

    @classmethod
    def render(cls) -> dict[str, Any]:
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


ToolDefinition = type[Tool] | JsonSchema
"""A tool can either be defined as a Pydantic model or directly as a json schema."""


@dataclass
class ToolCall:
    tool_name: BuiltInTool | str
    arguments: dict[str, str]

    def render(self) -> str:
        """Reconstruct the model response from a parsed tool call.

        There should only be one source of truth. As the response is stored in
        a parsed format, we need to convert it to a prompt string to construct
        the message history for a later interactions with the model.
        """
        if isinstance(self.tool_name, BuiltInTool):
            return SpecialTokens.PythonTag + self.render_build_in()
        else:
            # see `ToolCall.from_text` for why the python tag is not included here
            return self.render_json()

    def render_build_in(self) -> str:
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
            raise ValueError(f"Unknown built-in tool: {self.tool_name}")

    def render_json(self) -> str:
        return json.dumps(
            {"type": "function", "name": self.tool_name, "parameters": self.arguments}
        )

    @classmethod
    def from_response(cls, text: Response) -> "ToolCall | None":
        """Parse a tool call from a message that has been stripped of special tokens.

        While llama3.1 always include the <|python_tag|> prefix for function calls,
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
                tool_name=BuiltInTool.BraveSearch,
                arguments={
                    "query": text.split('brave_search.call(query="')[1]
                    .split('")')[0]
                    .strip()
                },
            )
        elif text.startswith("wolfram_alpha.call"):
            return ToolCall(
                tool_name=BuiltInTool.WolframAlpha,
                arguments={
                    "query": text.split('wolfram_alpha.call(query="')[1]
                    .split('")')[0]
                    .strip()
                },
            )
        else:
            return ToolCall(
                tool_name=BuiltInTool.CodeInterpreter,
                arguments={"code": text.strip()},
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


@dataclass
class ToolResponse:
    tool_name: BuiltInTool | str
    content: str
    success: bool = True

    def render(self) -> str:
        prompt = "completed" if self.success else "failed"
        if self.success:
            prompt += f"[stdout]{self.content}[/stdout]"
        else:
            prompt += f"[stderr]{self.content}[/stderr]"
        return prompt


def render_tool(tool: type[Tool] | JsonSchema) -> str:
    schema = tool if isinstance(tool, dict) else tool.render()
    return json.dumps(schema, indent=4)
