from dataclasses import dataclass


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
