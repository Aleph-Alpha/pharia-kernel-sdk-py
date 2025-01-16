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
from .tool import BraveSearch, CodeInterpreter, Tool, ToolDefinition, WolframAlpha


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
