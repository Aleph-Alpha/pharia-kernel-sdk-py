from pharia_skill.csi.chunking import ChunkParams, ChunkRequest
from pharia_skill.testing.dev.chunking import ChunkDeserializer, ChunkRequestSerializer

from .conftest import dumps


def test_serialize_chunk_request():
    # Given a chunk request
    request = ChunkRequestSerializer(
        requests=[
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
        {
            "requests": [
                {
                    "text": "Hello, world!",
                    "params": {
                        "model": "llama-3.1-8b-instruct",
                        "max_tokens": 100,
                        "overlap": 0,
                    },
                }
            ]
        }
    )


def test_deserialize_chunk_request():
    # Given a serialized chunk request
    serialized = dumps([["Hello, world!"]])

    # When deserializing it
    deserialized = ChunkDeserializer.model_validate_json(serialized)

    # Then we get a list of chunks
    assert len(deserialized.root) == 1
    assert deserialized.root[0][0] == "Hello, world!"
