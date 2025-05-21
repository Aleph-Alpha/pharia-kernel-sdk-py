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


@dataclass
class ToolCall:
    """A tool call as parsed from the response of the model.

    Arguments are not validated against the provided schema.
    """

    name: str
    parameters: dict[str, Any]

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
        cls, response: Response, tools: Sequence[str]
    ) -> "ToolCall | None":
        """Parse a tool call from a message that has been stripped of special tokens.

        Args:
            response (Response): The response of the model.
            tools (Sequence[str]): The tool names to use for parsing the tool call.
        """
        try:
            data = json.loads(response.text)
            name = data["name"]
            parameters = data["parameters"]
            tool = next((t for t in tools if t == name), None)
            if tool:
                return ToolCall(name, parameters)
        except (json.JSONDecodeError, KeyError):
            pass

        return None
