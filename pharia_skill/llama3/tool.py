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
from typing import Any, Literal

from pydantic import BaseModel


class BuiltInTool(str, Enum):
    CodeInterpreter = "code_interpreter"
    WolframAlpha = "wolfram_alpha"
    BraveSearch = "brave_search"


@dataclass
class ToolDefinition:
    """A tool can either be a built-in tool or a custom tool."""

    name: BuiltInTool | str
    description: str | None = None

    # the user can define parameters with a custom pydantic model
    parameters: type[BaseModel] | None = None

    def render(self) -> str:
        return json.dumps(self.as_dict(), indent=4)

    def as_dict(self) -> dict[str, Any]:
        if self.parameters:
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


@dataclass
class ToolCall:
    tool_name: BuiltInTool | str
    arguments: dict[str, str]

    def as_json(self) -> str:
        return json.dumps(
            {"type": "function", "name": self.tool_name, "parameters": self.arguments}
        )

    def render(self) -> str:
        """Reconstruct the model response from a parsed tool call.

        There should only be one source of truth. As the response is stored in
        a parsed format, we need to convert it to a prompt string to construct
        the message history for a later interactions with the model.
        """
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
            return self.as_json()


@dataclass
class ToolResponse:
    tool_name: BuiltInTool | str
    status: Literal["success", "failure"]
    # can be a any str representation of the output, e.g. '{"result": "[]"}'
    content: str

    def render(self) -> str:
        prompt = "completed" if self.status == "success" else "failed"
        if self.status == "success":
            prompt += f"[stdout]{self.content}[/stdout]"
        else:
            prompt += f"[stderr]{self.content}[/stderr]"
        return prompt
