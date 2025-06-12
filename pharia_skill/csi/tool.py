from pydantic.dataclasses import dataclass
from pydantic.types import JsonValue


@dataclass
class InvokeRequest:
    name: str
    arguments: dict[str, JsonValue]


@dataclass
class ToolOutput:
    """The output of a tool invocation.

    A tool result is a list of modalities.
    See <https://modelcontextprotocol.io/specification/2025-03-26/server/tools#tool-result>.
    At the moment, the Kernel only supports text modalities.

    Most tools will return a content list of size 1.
    """

    contents: list[str]
