from typing import Sequence

from pydantic import RootModel

from pharia_skill.csi import (
    Document,
    DocumentPath,
    JsonSerializable,
    SearchRequest,
    SearchResult,
)

DocumentMetadataSerializer = RootModel[Sequence[DocumentPath]]


DocumentMetadataDeserializer = RootModel[list[JsonSerializable | None]]


DocumentSerializer = RootModel[Sequence[DocumentPath]]


DocumentDeserializer = RootModel[list[Document]]


SearchRequestSerializer = RootModel[Sequence[SearchRequest]]


SearchResultDeserializer = RootModel[list[list[SearchResult]]]
