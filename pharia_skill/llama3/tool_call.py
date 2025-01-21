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
from typing import Any, Sequence

from .response import Response
from .tool import (
    BraveSearch,
    BuiltInTools,
    CodeInterpreter,
    Tool,
    ToolDefinition,
    WolframAlpha,
)


@dataclass
class ToolCall:
    """A tool call as parsed from the response of the model.

    Arguments are not validated against the provided schema.
    """

    name: str

    # tool is put second as for deserialization we always want the dict
    parameters: dict[str, Any] | Tool

    def render(self) -> str:
        """Reconstruct the model response from a parsed tool call.

        There should only be one source of truth. As the response is stored in
        a parsed format, we need to convert it to a prompt string to construct
        the message history for a later interactions with the model.
        """
        if isinstance(self.parameters, dict):
            return json.dumps({"name": self.name, "parameters": self.parameters})
        return self.parameters.render()

    @classmethod
    def from_response(
        cls, text: Response, tools: Sequence[ToolDefinition]
    ) -> "ToolCall | None":
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
            return cls.json_from_text(text.text, tools) or cls.built_in_from_text(
                text.text, tools
            )
        else:
            return cls.json_from_text(text.text, tools)

    @staticmethod
    def built_in_from_text(
        text: str, tools: Sequence[ToolDefinition]
    ) -> "ToolCall | None":
        """Parse a tool call from a message that started with the Python Tag."""
        if BraveSearch in tools and (brave_search := BraveSearch.try_from_text(text)):
            return ToolCall("brave_search", brave_search)
        elif WolframAlpha in tools and (wolfram := WolframAlpha.try_from_text(text)):
            return ToolCall("wolfram_alpha", wolfram)
        elif CodeInterpreter in tools:
            return ToolCall("code_interpreter", CodeInterpreter(src=text.strip()))
        return None

    @classmethod
    def json_from_text(
        cls, response: str, tools: Sequence[ToolDefinition]
    ) -> "ToolCall | None":
        """Try parsing a tool call into one of the user provided tools.

        Raise a pydantic validation error if the model tries a call that
        can not be parsed into the provided schema.
        """
        try:
            data = json.loads(response)
            name = data["name"]
            parameters = data["parameters"]
            tool = next(
                (t for t in tools if t.name() == name and t not in BuiltInTools), None
            )
            if tool:
                if isinstance(tool, type):
                    parameters = tool(**parameters)

                return ToolCall(name, parameters)
        except (json.JSONDecodeError, KeyError):
            pass

        return None
