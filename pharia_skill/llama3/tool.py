"""
Tools integrate LLMs with external services.

For this, three points of interactions are needed, which are represented by three
classes in this module.

1. The model needs to know a about the available tools (`ToolDefinition`).
2. The model needs to be able to call a tool (`ToolCall`).
3. The model needs to know th result of the tool call (`ToolResponse`).
"""

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any

from pydantic import BaseModel, model_serializer, model_validator

from .response import Response


class BuiltInTool(str, Enum):
    CodeInterpreter = "code_interpreter"
    WolframAlpha = "wolfram_alpha"
    BraveSearch = "brave_search"


class ToolDefinition(BaseModel):
    """Provide context on a tool that can be called by the model.

    A tool can be setup from a json schema or by directly providing its name,
    definition and parameters. The parameters can be provided as a pydantic model,
    allowing the user to not worry about writing json schema. The type of the each
    parameter is automatically inferred from the pydantic model. Here is an example
    of a definition that would render to json schema with three fields. The schema
    would have a description for the repository field and a default value for the
    tag field.

    Example::

        from pydantic import BaseMode, Field

        class Parameters(BaseModel):
            registry: str
            repository: str = Field(
                description="The name of the GitHub repository to get the readme from",
            )
            tag: str = "latest"


    """

    name: BuiltInTool | str
    description: str | None = None
    parameters: type[BaseModel] | dict[str, Any] | None = None

    def render(self) -> str:
        return json.dumps(self.as_dict(), indent=4)

    @model_serializer
    def as_dict(self) -> dict[str, Any]:
        """Json Schema serialiation for a `ToolDefinition`.

        Pydantic is not able to serialize a model meta class to a dictionary.
        Therefore, the json schema is also set as the default way to serialize
        a `ToolDefinition`.
        """
        if isinstance(self.parameters, dict):
            parameters = self.parameters
        elif isinstance(self.parameters, type):
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

    @model_validator(mode="before")  # pyright: ignore
    @classmethod
    def deserialize(cls, values: Any) -> Any:
        """Custom deserialization for a `ToolDefinition`.

        Tool definition can be provided in two ways:

        1. From a json schema (e.g.) if the definition is coming via HTTP.
        2. With a Pydantic model, if the definition is provided in code.

        While a `ToolDefinition` will render to a json schema definition building on
        pydantic.model_json_schema, it also needs to be able to load from a json schema.

        Therefore, the values need to be augmented in the deserialization step.
        """
        if values.get("function") is not None:
            if values.get("name") is None:
                values["name"] = values["function"]["name"]
            if values.get("description") is None:
                values["description"] = values["function"]["description"]
            if values.get("parameters") is None:
                values["parameters"] = values["function"]["parameters"]
        return values


PythonTag = "<|python_tag|>"
"""Python tag that is used to indicate that the message is a tool call."""


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
            return PythonTag + self.render_build_in()
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
