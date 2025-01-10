"""
This module encapsulates knowledge about the structure of llama3 prompts and responses.
"""

from enum import Enum
from typing import NamedTuple


class SpecialTokens(str, Enum):
    EndOfTurn = "<|eot_id|>"
    EndOfMessage = "<|eom_id|>"
    PythonTag = "<|python_tag|>"
    BeginOfText = "<|begin_of_text|>"


RawResponse = str
"""Unparsed response as received from the model.

Contains special tokens and whitespace.
"""


class Response(NamedTuple):
    """Inner part of the completion.

    The text is stripped from all special tokens and stop reasons.
    Information about the presence of the Python tag is stored in a separate attribute.
    """

    text: str
    python_tag: bool

    @staticmethod
    def from_raw(raw: RawResponse) -> "Response":
        raw = raw.replace(SpecialTokens.EndOfTurn, "")
        raw = raw.replace(SpecialTokens.EndOfMessage, "")
        raw = raw.strip()
        python_tag = raw.startswith(SpecialTokens.PythonTag)
        text = raw.replace(SpecialTokens.PythonTag, "")
        return Response(text, python_tag)
