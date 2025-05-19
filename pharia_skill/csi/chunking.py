from dataclasses import asdict
from typing import Any

from pydantic import model_serializer

# We use pydantic.dataclasses to get type validation.
# See the docstring of `csi` module for more information on the why.
from pydantic.dataclasses import dataclass


@dataclass
class ChunkParams:
    """Chunking parameters.

    Attributes:
        model (str, required): The name of the model the chunk is intended to be used for. This must be a known model.
        max_tokens (int, required): The maximum number of tokens that should be returned per chunk.
        overlap (int, optional, default 0): The amount of allowed overlap between chunks. Must be less than max_tokens. By default, there is no overlap between chunks.
    """

    model: str
    max_tokens: int
    overlap: int = 0


@dataclass
class ChunkRequest:
    """Chunking request parameters.

    Attributes:
        text (str, required): The text to be chunked.
        params (ChunkParams, required): Parameter used for chunking.
    """

    text: str
    params: ChunkParams

    @model_serializer()
    def serialize(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "params": asdict(self.params),
            "character_offsets": True,
        }


@dataclass
class Chunk:
    """Chunk object with offset information.

    Attributes:
        text (str, required): The text that was chunked
        character_offset (int, required): The character offset relative to the start of the original text
    """

    text: str
    character_offset: int
