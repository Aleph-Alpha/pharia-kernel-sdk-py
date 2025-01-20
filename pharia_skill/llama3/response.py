"""
This module encapsulates knowledge about the structure of llama3 prompts and responses.
"""

from dataclasses import dataclass
from enum import Enum


class SpecialTokens(str, Enum):
    EndOfTurn = "<|eot_id|>"
    EndOfMessage = "<|eom_id|>"
    PythonTag = "<|python_tag|>"
    BeginOfText = "<|begin_of_text|>"
    StartHeader = "<|start_header_id|>"
    EndHeader = "<|end_header_id|>"


RawResponse = str
"""Unparsed response as received from the model.

Contains special tokens and whitespace.
"""


@dataclass(frozen=True)
class Response:
    """Inner part of the completion.

    The text is stripped from all special tokens and stop reasons.
    Information about the presence of the Python tag is stored in a separate attribute.
    """

    text: str
    python_tag: bool

    @staticmethod
    def from_raw(raw: RawResponse) -> "Response":
        """Parse a raw response (as received from the model)."""
        raw = raw.replace(SpecialTokens.EndOfTurn, "")
        raw = raw.replace(SpecialTokens.EndOfMessage, "")

        # Strip all whitespace from the message.
        # We assume that no model response or tool call should
        # start or end with whitespace.
        raw = raw.strip()
        python_tag = raw.startswith(SpecialTokens.PythonTag)
        text = raw.replace(SpecialTokens.PythonTag, "")
        return Response(text, python_tag)
