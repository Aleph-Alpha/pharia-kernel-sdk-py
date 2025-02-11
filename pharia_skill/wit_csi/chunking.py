from ..csi.chunking import ChunkParams, ChunkRequest
from ..wit.imports.chunking import ChunkParams as WitChunkParams
from ..wit.imports.chunking import ChunkRequest as WitChunkRequest


def chunk_params_to_wit(chunk_params: ChunkParams) -> WitChunkParams:
    return WitChunkParams(
        model=chunk_params.model,
        max_tokens=chunk_params.max_tokens,
        overlap=chunk_params.overlap,
    )


def chunk_request_to_wit(chunk_request: ChunkRequest) -> WitChunkRequest:
    return WitChunkRequest(
        text=chunk_request.text, params=chunk_params_to_wit(chunk_request.params)
    )
