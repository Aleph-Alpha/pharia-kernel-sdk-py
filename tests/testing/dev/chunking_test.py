from pharia_skill.csi.chunking import Chunk, ChunkParams, ChunkRequest
from pharia_skill.testing.dev.chunking import (
    ChunkDeserializer,
    ChunkRequestSerializer,
)

from .conftest import dumps


def test_serialize_chunk_request():
    # Given a chunk request
    request = ChunkRequestSerializer(
        [
            ChunkRequest(
                text="Hello, world!",
                params=ChunkParams(model="llama-3.1-8b-instruct", max_tokens=100),
            )
        ]
    )

    # When serializing it
    serialized = request.model_dump_json()

    # Then it nests the structure
    assert serialized == dumps(
        [
            {
                "text": "Hello, world!",
                "params": {
                    "model": "llama-3.1-8b-instruct",
                    "max_tokens": 100,
                    "overlap": 0,
                },
                "character_offsets": True,
            }
        ]
    )


def test_deserialize_chunk_response():
    # Given a serialized chunk response
    serialized = dumps(
        [[{"text": "Hello, world!", "byte_offset": 42, "character_offset": 10}]]
    )

    # When deserializing it
    deserialized = ChunkDeserializer.model_validate_json(serialized)

    # Then we get a list of chunks
    assert len(deserialized.root) == 1
    assert deserialized.root[0][0] == Chunk(text="Hello, world!", offset=10)
