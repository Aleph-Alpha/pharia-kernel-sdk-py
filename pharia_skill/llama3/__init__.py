"""Tool calling functionality for the llama3 models.

.. warning::
   **Deprecated:** This module is deprecated and will be removed in the future.
   Use the tool calling functionality offered by the chat methods on the `Csi`
   interface instead.
"""

import warnings

from .message import AssistantMessage, Role, ToolMessage, UserMessage
from .request import ChatRequest, ChatResponse
from .response import SpecialTokens
from .tool import (
    BraveSearch,
    CodeInterpreter,
    JsonSchema,
    Tool,
    ToolDefinition,
    WolframAlpha,
)
from .tool_call import ToolCall

__all__ = [
    "ChatRequest",
    "ChatResponse",
    "UserMessage",
    "Role",
    "AssistantMessage",
    "ToolCall",
    "ToolDefinition",
    "ToolMessage",
    "BraveSearch",
    "SpecialTokens",
    "JsonSchema",
    "CodeInterpreter",
    "WolframAlpha",
    "Tool",
]

warnings.warn(
    "The `llama3` module is deprecated and will be removed in the future. "
    "Use the tool calling functionality offered by the chat methods on the `Csi` "
    "interface instead.",
    DeprecationWarning,
    stacklevel=2,
)
