from ..bindings.imports import chunking as wit
from ..csi.chunking import Chunk, ChunkParams, ChunkRequest


def chunk_params_to_wit(chunk_params: ChunkParams) -> wit.ChunkParams:
    return wit.ChunkParams(
        model=chunk_params.model,
        max_tokens=chunk_params.max_tokens,
        overlap=chunk_params.overlap,
    )


def chunk_request_to_wit(
    chunk_request: ChunkRequest,
) -> wit.ChunkWithOffsetRequest:
    return wit.ChunkWithOffsetRequest(
        text=chunk_request.text,
        params=chunk_params_to_wit(chunk_request.params),
        character_offsets=True,
    )


def chunk_from_wit(chunk: wit.ChunkWithOffset) -> Chunk:
    # The character offset is always expected becaused the flag `character_offsets` is enabled
    assert chunk.character_offset is not None
    return Chunk(text=chunk.text, offset=chunk.character_offset)
