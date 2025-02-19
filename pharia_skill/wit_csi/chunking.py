from ..csi.chunking import ChunkParams, ChunkRequest
from ..wit.imports import chunking as wit


def chunk_params_to_wit(chunk_params: ChunkParams) -> wit.ChunkParams:
    return wit.ChunkParams(
        model=chunk_params.model,
        max_tokens=chunk_params.max_tokens,
        overlap=chunk_params.overlap,
    )


def chunk_request_to_wit(chunk_request: ChunkRequest) -> wit.ChunkRequest:
    return wit.ChunkRequest(
        text=chunk_request.text, params=chunk_params_to_wit(chunk_request.params)
    )
