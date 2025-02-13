from pydantic import BaseModel, RootModel

from pharia_skill.csi import (
    Document,
    DocumentPath,
    JsonSerializable,
    SearchRequest,
    SearchResult,
)


class DocumentMetadataSerializer(BaseModel):
    requests: list[DocumentPath]


DocumentMetadataDeserializer = RootModel[list[JsonSerializable | None]]


class DocumentSerializer(BaseModel):
    requests: list[DocumentPath]


DocumentDeserializer = RootModel[list[Document]]


class SearchRequestSerializer(BaseModel):
    requests: list[SearchRequest]


SearchResultDeserializer = RootModel[list[list[SearchResult]]]
