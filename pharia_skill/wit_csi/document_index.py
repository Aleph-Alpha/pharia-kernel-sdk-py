import datetime as dt
import json
from typing import cast

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
from ..wit.imports.document_index import Document as WitDocument
from ..wit.imports.document_index import DocumentPath as WitDocumentPath
from ..wit.imports.document_index import IndexPath as WitIndexPath
from ..wit.imports.document_index import MetadataFieldValue as WitMetadataFieldValue
from ..wit.imports.document_index import (
    MetadataFieldValue_BooleanType as WitMetadataFieldValue_BooleanType,
)
from ..wit.imports.document_index import (
    MetadataFieldValue_IntegerType as WitMetadataFieldValue_IntegerType,
)
from ..wit.imports.document_index import (
    MetadataFieldValue_StringType as WitMetadataFieldValue_StringType,
)
from ..wit.imports.document_index import MetadataFilter as WitMetadataFilter
from ..wit.imports.document_index import (
    MetadataFilterCondition as WitMetadataFilterCondition,
)
from ..wit.imports.document_index import (
    MetadataFilterCondition_After as WitMetadataFilterCondition_After,
)
from ..wit.imports.document_index import (
    MetadataFilterCondition_AtOrAfter as WitMetadataFilterCondition_AtOrAfter,
)
from ..wit.imports.document_index import (
    MetadataFilterCondition_AtOrBefore as WitMetadataFilterCondition_AtOrBefore,
)
from ..wit.imports.document_index import (
    MetadataFilterCondition_Before as WitMetadataFilterCondition_Before,
)
from ..wit.imports.document_index import (
    MetadataFilterCondition_EqualTo as WitMetadataFilterCondition_EqualTo,
)
from ..wit.imports.document_index import (
    MetadataFilterCondition_GreaterThan as WitMetadataFilterCondition_GreaterThan,
)
from ..wit.imports.document_index import (
    MetadataFilterCondition_GreaterThanOrEqualTo as WitMetadataFilterCondition_GreaterThanOrEqualTo,
)
from ..wit.imports.document_index import (
    MetadataFilterCondition_IsNull as WitMetadataFilterCondition_IsNull,
)
from ..wit.imports.document_index import (
    MetadataFilterCondition_LessThan as WitMetadataFilterCondition_LessThan,
)
from ..wit.imports.document_index import (
    MetadataFilterCondition_LessThanOrEqualTo as WitMetadataFilterCondition_LessThanOrEqualTo,
)
from ..wit.imports.document_index import Modality as WitModality
from ..wit.imports.document_index import Modality_Text as WitText
from ..wit.imports.document_index import SearchFilter as WitSearchFilter
from ..wit.imports.document_index import SearchFilter_WithAll as WitSearchFilter_WithAll
from ..wit.imports.document_index import (
    SearchFilter_WithOneOf as WitSearchFilter_WithOneOf,
)
from ..wit.imports.document_index import SearchFilter_Without as WitSearchFilter_Without
from ..wit.imports.document_index import SearchRequest as WitSearchRequest
from ..wit.imports.document_index import SearchResult as WitSearchResult
from ..wit.imports.document_index import TextCursor as WitCursor


def to_isostring(datetime: dt.datetime) -> str:
    """The WIT world represents instants as ISO 8601 strings.

    While the Document Index supports loading from any timezoned string, we do require specifying as timezone.
    """
    assert datetime.tzinfo is not None, "Datetimes must be timezone-aware"
    return datetime.isoformat()


def value_to_wit(value: str | int | bool) -> WitMetadataFieldValue:
    match value:
        case str():
            return WitMetadataFieldValue_StringType(value)
        case int():
            return WitMetadataFieldValue_IntegerType(value)
        case bool():
            return WitMetadataFieldValue_BooleanType(value)


def condition_to_wit(condition: FilterCondition) -> WitMetadataFilterCondition:
    match condition:
        case GreaterThan(value):
            return WitMetadataFilterCondition_GreaterThan(value)
        case GreaterThanOrEqualTo(value):
            return WitMetadataFilterCondition_GreaterThanOrEqualTo(value)
        case LessThan(value):
            return WitMetadataFilterCondition_LessThan(value)
        case LessThanOrEqualTo(value):
            return WitMetadataFilterCondition_LessThanOrEqualTo(value)
        case After(value):
            return WitMetadataFilterCondition_After(to_isostring(value))
        case AtOrAfter(value):
            return WitMetadataFilterCondition_AtOrAfter(to_isostring(value))
        case Before(value):
            return WitMetadataFilterCondition_Before(to_isostring(value))
        case AtOrBefore(value):
            return WitMetadataFilterCondition_AtOrBefore(to_isostring(value))
        case EqualTo(value):
            return WitMetadataFilterCondition_EqualTo(value_to_wit(value))
        case IsNull():
            return WitMetadataFilterCondition_IsNull()


def metadata_filter_to_wit(filter: MetadataFilter) -> WitMetadataFilter:
    return WitMetadataFilter(
        field=filter.field,
        condition=condition_to_wit(filter.condition),
    )


def filter_to_wit(filter: SearchFilter) -> WitSearchFilter:
    match filter:
        case Without(value):
            return WitSearchFilter_Without(
                value=[metadata_filter_to_wit(f) for f in value]
            )
        case WithOneOf(value):
            return WitSearchFilter_WithOneOf(
                value=[metadata_filter_to_wit(f) for f in value]
            )
        case With(value):
            return WitSearchFilter_WithAll(
                value=[metadata_filter_to_wit(f) for f in value]
            )


def search_request_to_wit(request: SearchRequest) -> WitSearchRequest:
    return WitSearchRequest(
        index_path=index_path_to_wit(request.index_path),
        query=request.query,
        max_results=request.max_results,
        min_score=request.min_score,
        filters=[filter_to_wit(f) for f in request.filters],
    )


def document_path_from_wit(document_path: WitDocumentPath) -> DocumentPath:
    return DocumentPath(
        namespace=document_path.namespace,
        collection=document_path.collection,
        name=document_path.name,
    )


def cursor_from_wit(cursor: WitCursor) -> Cursor:
    return Cursor(item=cursor.item, position=cursor.position)


def search_result_from_wit(result: WitSearchResult) -> SearchResult:
    return SearchResult(
        document_path=document_path_from_wit(result.document_path),
        content=result.content,
        score=result.score,
        start=cursor_from_wit(result.start),
        end=cursor_from_wit(result.end),
    )


def document_path_to_wit(document_path: DocumentPath) -> WitDocumentPath:
    return WitDocumentPath(
        namespace=document_path.namespace,
        collection=document_path.collection,
        name=document_path.name,
    )


def document_contents_from_wit(contents: list[WitModality]) -> list[Modality]:
    return [
        Text(content.value) if isinstance(content, WitText) else Image()
        for content in contents
    ]


def document_metadata_from_wit(metadata: bytes | None) -> JsonSerializable:
    return cast(JsonSerializable, json.loads(metadata)) if metadata else None


def document_from_wit(document: WitDocument) -> Document:
    metadata = document_metadata_from_wit(document.metadata)
    contents = document_contents_from_wit(document.contents)
    path = document_path_from_wit(document.path)
    return Document(path=path, contents=contents, metadata=metadata)


def index_path_to_wit(index_path: IndexPath) -> WitIndexPath:
    return WitIndexPath(
        namespace=index_path.namespace,
        collection=index_path.collection,
        index=index_path.index,
    )
