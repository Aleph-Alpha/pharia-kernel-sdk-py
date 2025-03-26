import datetime as dt
import json
from typing import cast

from ..bindings.imports import document_index as wit
from ..csi import (
    After,
    AtOrAfter,
    AtOrBefore,
    Before,
    Cursor,
    Document,
    DocumentPath,
    EqualTo,
    FilterCondition,
    GreaterThan,
    GreaterThanOrEqualTo,
    Image,
    IndexPath,
    IsNull,
    JsonSerializable,
    LessThan,
    LessThanOrEqualTo,
    MetadataFilter,
    Modality,
    SearchFilter,
    SearchRequest,
    SearchResult,
    Text,
    With,
    WithOneOf,
    Without,
)


def to_isostring(datetime: dt.datetime) -> str:
    """The WIT world represents instants as ISO 8601 strings.

    While the Document Index supports loading from any timezoned string, we do require specifying as timezone.
    """
    assert datetime.tzinfo is not None, "Datetimes must be timezone-aware"
    return datetime.isoformat()


def value_to_wit(value: str | int | bool) -> wit.MetadataFieldValue:
    match value:
        case str():
            return wit.MetadataFieldValue_StringType(value)
        case int():
            return wit.MetadataFieldValue_IntegerType(value)
        case bool():
            return wit.MetadataFieldValue_BooleanType(value)


def condition_to_wit(condition: FilterCondition) -> wit.MetadataFilterCondition:
    match condition:
        case GreaterThan(value):
            return wit.MetadataFilterCondition_GreaterThan(value)
        case GreaterThanOrEqualTo(value):
            return wit.MetadataFilterCondition_GreaterThanOrEqualTo(value)
        case LessThan(value):
            return wit.MetadataFilterCondition_LessThan(value)
        case LessThanOrEqualTo(value):
            return wit.MetadataFilterCondition_LessThanOrEqualTo(value)
        case After(value):
            return wit.MetadataFilterCondition_After(to_isostring(value))
        case AtOrAfter(value):
            return wit.MetadataFilterCondition_AtOrAfter(to_isostring(value))
        case Before(value):
            return wit.MetadataFilterCondition_Before(to_isostring(value))
        case AtOrBefore(value):
            return wit.MetadataFilterCondition_AtOrBefore(to_isostring(value))
        case EqualTo(value):
            return wit.MetadataFilterCondition_EqualTo(value_to_wit(value))
        case IsNull():
            return wit.MetadataFilterCondition_IsNull()


def metadata_filter_to_wit(filter: MetadataFilter) -> wit.MetadataFilter:
    return wit.MetadataFilter(
        field=filter.field,
        condition=condition_to_wit(filter.condition),
    )


def filter_to_wit(filter: SearchFilter) -> wit.SearchFilter:
    match filter:
        case Without(value):
            return wit.SearchFilter_Without(
                value=[metadata_filter_to_wit(f) for f in value]
            )
        case WithOneOf(value):
            return wit.SearchFilter_WithOneOf(
                value=[metadata_filter_to_wit(f) for f in value]
            )
        case With(value):
            return wit.SearchFilter_WithAll(
                value=[metadata_filter_to_wit(f) for f in value]
            )


def search_request_to_wit(request: SearchRequest) -> wit.SearchRequest:
    return wit.SearchRequest(
        index_path=index_path_to_wit(request.index_path),
        query=request.query,
        max_results=request.max_results,
        min_score=request.min_score,
        filters=[filter_to_wit(f) for f in request.filters],
    )


def document_path_from_wit(document_path: wit.DocumentPath) -> DocumentPath:
    return DocumentPath(
        namespace=document_path.namespace,
        collection=document_path.collection,
        name=document_path.name,
    )


def cursor_from_wit(cursor: wit.TextCursor) -> Cursor:
    return Cursor(item=cursor.item, position=cursor.position)


def search_result_from_wit(result: wit.SearchResult) -> SearchResult:
    return SearchResult(
        document_path=document_path_from_wit(result.document_path),
        content=result.content,
        score=result.score,
        start=cursor_from_wit(result.start),
        end=cursor_from_wit(result.end),
    )


def document_path_to_wit(document_path: DocumentPath) -> wit.DocumentPath:
    return wit.DocumentPath(
        namespace=document_path.namespace,
        collection=document_path.collection,
        name=document_path.name,
    )


def document_contents_from_wit(contents: list[wit.Modality]) -> list[Modality]:
    return [
        Text(content.value) if isinstance(content, wit.Modality_Text) else Image()
        for content in contents
    ]


def document_metadata_from_wit(metadata: bytes | None) -> JsonSerializable:
    return cast(JsonSerializable, json.loads(metadata)) if metadata else None


def document_from_wit(document: wit.Document) -> Document:
    metadata = document_metadata_from_wit(document.metadata)
    contents = document_contents_from_wit(document.contents)
    path = document_path_from_wit(document.path)
    return Document(path=path, contents=contents, metadata=metadata)


def index_path_to_wit(index_path: IndexPath) -> wit.IndexPath:
    return wit.IndexPath(
        namespace=index_path.namespace,
        collection=index_path.collection,
        index=index_path.index,
    )
