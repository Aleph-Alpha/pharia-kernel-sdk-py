import datetime as dt

from pharia_skill import (
    After,
    Cursor,
    Document,
    DocumentPath,
    IndexPath,
    MetadataFilter,
    SearchRequest,
    SearchResult,
    Text,
    With,
    WithOneOf,
)
from pharia_skill.testing.dev.document_index import (
    DocumentDeserializer,
    DocumentMetadataDeserializer,
    DocumentMetadataSerializer,
    DocumentSerializer,
    SearchRequestSerializer,
    SearchResultDeserializer,
)

from .conftest import dumps


def test_serialize_document_metadata_request():
    # Given a document metadata request
    request = DocumentMetadataSerializer(
        [
            DocumentPath(
                namespace="test",
                collection="kernel",
                name="docs",
            )
        ]
    )

    # When serializing it
    serialized = request.model_dump_json()

    # Then it nests the structure
    assert serialized == dumps(
        [
            {
                "namespace": "test",
                "collection": "kernel",
                "name": "docs",
            }
        ]
    )


def test_deserialize_document_metadata():
    # Given a serialized document metadata request
    serialized = dumps(
        [
            {
                "created": "2025-01-01T00:00:00Z",
                "url": "https://pharia-kernel.product.pharia.com/",
            }
        ]
    )

    # When deserializing it
    deserialized = DocumentMetadataDeserializer.model_validate_json(serialized)
    metadata = deserialized.root[0]

    # Then the document metadata is loaded recursively
    assert metadata == {
        "created": "2025-01-01T00:00:00Z",
        "url": "https://pharia-kernel.product.pharia.com/",
    }


def test_serialize_document_request():
    # Given a document request
    request = DocumentSerializer(
        root=[
            DocumentPath(
                namespace="test",
                collection="kernel",
                name="docs",
            )
        ]
    )

    # When serializing it
    serialized = request.model_dump_json()

    # Then
    assert serialized == dumps(
        [
            {
                "namespace": "test",
                "collection": "kernel",
                "name": "docs",
            }
        ]
    )


def test_deserialize_document():
    # Given a serialized document request
    serialized = dumps(
        [
            {
                "contents": [
                    {
                        "modality": "text",
                        "text": "You might be wondering what the Kernel is.",
                    }
                ],
                "metadata": {
                    "created": "2025-01-01T00:00:00Z",
                    "url": "https://pharia-kernel.product.pharia.com/",
                },
                "path": {
                    "collection": "test",
                    "name": "kernel/docs",
                    "namespace": "Kernel",
                },
            }
        ]
    )

    # When deserializing it
    deserialized = DocumentDeserializer.model_validate_json(serialized)
    document = deserialized.root[0]

    # Then the document is loaded correctly
    assert document == Document(
        path=DocumentPath(namespace="Kernel", collection="test", name="kernel/docs"),
        contents=[Text(text="You might be wondering what the Kernel is.")],
        metadata={
            "created": "2025-01-01T00:00:00Z",
            "url": "https://pharia-kernel.product.pharia.com/",
        },
    )


def test_serialize_search_request():
    # Given a list of search requests
    request = SearchRequestSerializer(
        [
            SearchRequest(
                index_path=IndexPath(
                    namespace="Kernel", collection="test", index="asym-64"
                ),
                query="What is the Kernel?",
                filters=[
                    With(
                        [
                            MetadataFilter(
                                field="created",
                                condition=After(
                                    value=dt.datetime(
                                        1970, 7, 1, 14, 10, 11, tzinfo=dt.UTC
                                    )
                                ),
                            )
                        ]
                    ),
                    WithOneOf(
                        [
                            MetadataFilter(
                                field="created",
                                condition=After(
                                    value=dt.datetime(
                                        1970, 7, 1, 14, 10, 11, tzinfo=dt.UTC
                                    )
                                ),
                            )
                        ]
                    ),
                ],
            )
        ]
    )

    # When serializing it
    serialized = request.model_dump_json()

    # Then
    assert serialized == dumps(
        [
            {
                "index_path": {
                    "namespace": "Kernel",
                    "collection": "test",
                    "index": "asym-64",
                },
                "query": "What is the Kernel?",
                "max_results": 1,
                "min_score": None,
                "filters": [
                    {
                        "with": [
                            {
                                "metadata": {
                                    "field": "created",
                                    "after": "1970-07-01T14:10:11Z",
                                }
                            }
                        ]
                    },
                    {
                        "with_one_of": [
                            {
                                "metadata": {
                                    "field": "created",
                                    "after": "1970-07-01T14:10:11Z",
                                }
                            }
                        ]
                    },
                ],
            }
        ]
    )


def test_deserialize_search_response():
    # Given a serialized search response
    serialized = dumps(
        [
            [
                {
                    "content": "You might be wondering what the Kernel is.",
                    "document_path": {
                        "collection": "test",
                        "name": "kernel docs",
                        "namespace": "Kernel",
                    },
                    "end": {"item": 0, "position": 243},
                    "score": 0.748,
                    "start": {"item": 0, "position": 0},
                }
            ]
        ]
    )

    # When deserializing it
    deserialized = SearchResultDeserializer.model_validate_json(serialized)
    search_result = deserialized.root[0][0]

    # Then the search result is loaded correctly
    assert search_result == SearchResult(
        document_path=DocumentPath(
            namespace="Kernel", collection="test", name="kernel docs"
        ),
        content="You might be wondering what the Kernel is.",
        score=0.748,
        start=Cursor(item=0, position=0),
        end=Cursor(item=0, position=243),
    )
