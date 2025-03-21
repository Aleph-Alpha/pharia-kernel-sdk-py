from pydantic import RootModel

from pharia_skill.csi import (
    Document,
    DocumentPath,
    JsonSerializable,
    SearchRequest,
    SearchResult,
)

DocumentMetadataSerializer = RootModel[list[DocumentPath]]


DocumentMetadataDeserializer = RootModel[list[JsonSerializable | None]]


DocumentSerializer = RootModel[list[DocumentPath]]


DocumentDeserializer = RootModel[list[Document]]


SearchRequestSerializer = RootModel[list[SearchRequest]]


SearchResultDeserializer = RootModel[list[list[SearchResult]]]
