import datetime as dt
from typing import Any

from pydantic import BaseModel, Field, RootModel

from pharia_skill.csi import (
    After,
    AtOrAfter,
    AtOrBefore,
    Before,
    Document,
    DocumentPath,
    EqualTo,
    GreaterThan,
    GreaterThanOrEqualTo,
    IndexPath,
    IsNull,
    JsonSerializable,
    LessThan,
    LessThanOrEqualTo,
    MetadataFilter,
    SearchFilter,
    SearchRequest,
    SearchResult,
    WithAll,
    WithOneOf,
    Without,
)


class DocumentMetadataSerializer(BaseModel):
    requests: list[DocumentPath]


DocumentMetadataDeserializer = RootModel[list[JsonSerializable | None]]


class DocumentSerializer(BaseModel):
    requests: list[DocumentPath]


DocumentDeserializer = RootModel[list[Document]]


def to_isostring(datetime: dt.datetime) -> str:
    """The WIT world represents instants as ISO 8601 strings.

    While the Document Index supports loading from any timezoned string, we do require specifying as timezone.
    """
    assert datetime.tzinfo is not None, "Datetimes must be timezone-aware"
    return datetime.isoformat()


class AfterSerializer(BaseModel):
    field: str
    after: str


class BeforeSerializer(BaseModel):
    field: str
    before: str


class AtOrAfterSerializer(BaseModel):
    field: str
    at_or_after: str


class AtOrBeforeSerializer(BaseModel):
    field: str
    at_or_before: str


class EqualToSerializer(BaseModel):
    field: str
    equal_to: Any


class GreaterThanSerializer(BaseModel):
    field: str
    greater_than: float


class GreaterThanOrEqualToSerializer(BaseModel):
    field: str
    greater_than_or_equal_to: float


class LessThanSerializer(BaseModel):
    field: str
    less_than: float


class LessThanOrEqualToSerializer(BaseModel):
    field: str
    less_than_or_equal_to: float


class IsNullSerializer(BaseModel):
    field: str
    is_null: bool


FilterSerializer = (
    AfterSerializer
    | BeforeSerializer
    | AtOrAfterSerializer
    | AtOrBeforeSerializer
    | EqualToSerializer
    | GreaterThanSerializer
    | GreaterThanOrEqualToSerializer
    | LessThanSerializer
    | LessThanOrEqualToSerializer
    | IsNullSerializer
)


def from_metadata_filter(filter: MetadataFilter) -> FilterSerializer:
    match filter.condition:
        case After(value):
            return AfterSerializer(field=filter.field, after=to_isostring(value))
        case Before(value):
            return BeforeSerializer(field=filter.field, before=to_isostring(value))
        case AtOrAfter(value):
            return AtOrAfterSerializer(
                field=filter.field, at_or_after=to_isostring(value)
            )
        case AtOrBefore(value):
            return AtOrBeforeSerializer(
                field=filter.field, at_or_before=to_isostring(value)
            )
        case EqualTo(value):
            return EqualToSerializer(field=filter.field, equal_to=value)
        case GreaterThan(value):
            return GreaterThanSerializer(field=filter.field, greater_than=value)
        case GreaterThanOrEqualTo(value):
            return GreaterThanOrEqualToSerializer(
                field=filter.field, greater_than_or_equal_to=value
            )
        case LessThan(value):
            return LessThanSerializer(field=filter.field, less_than=value)
        case LessThanOrEqualTo(value):
            return LessThanOrEqualToSerializer(
                field=filter.field, less_than_or_equal_to=value
            )
        case IsNull():
            return IsNullSerializer(field=filter.field, is_null=True)


class MetadataFilterModel(BaseModel):
    metadata: (
        AfterSerializer
        | BeforeSerializer
        | AtOrAfterSerializer
        | AtOrBeforeSerializer
        | EqualToSerializer
        | GreaterThanSerializer
        | GreaterThanOrEqualToSerializer
        | LessThanSerializer
        | LessThanOrEqualToSerializer
        | IsNullSerializer
    )


class WithAllSerializer(BaseModel):
    with_: list[MetadataFilterModel] = Field(serialization_alias="with")


class WithOneOfFilter(BaseModel):
    with_one_of: list[MetadataFilterModel]


class WithoutFilter(BaseModel):
    without: list[MetadataFilterModel]


def from_search_filter(
    filter: SearchFilter,
) -> "WithAllSerializer | WithOneOfFilter | WithoutFilter":
    match filter:
        case WithAll(value):
            metadata_filters = [
                MetadataFilterModel(metadata=from_metadata_filter(f)) for f in value
            ]
            return WithAllSerializer(with_=metadata_filters)

        case WithOneOf(value):
            metadata_filters = [
                MetadataFilterModel(metadata=from_metadata_filter(f)) for f in value
            ]
            return WithOneOfFilter(with_one_of=metadata_filters)

        case Without(value):
            metadata_filters = [
                MetadataFilterModel(metadata=from_metadata_filter(f)) for f in value
            ]
            return WithoutFilter(without=metadata_filters)


class SearchRequestModel(BaseModel):
    index_path: IndexPath
    query: str
    max_results: int
    min_score: float | None
    filters: list[WithAllSerializer | WithOneOfFilter | WithoutFilter]

    @classmethod
    def from_search_request(cls, request: SearchRequest) -> "SearchRequestModel":
        return cls(
            index_path=request.index_path,
            query=request.query,
            max_results=request.max_results,
            min_score=request.min_score,
            filters=[from_search_filter(f) for f in request.filters],
        )


class SearchRequestSerializer(BaseModel):
    requests: list[SearchRequestModel]

    @classmethod
    def from_search_requests(
        cls, requests: list[SearchRequest]
    ) -> "SearchRequestSerializer":
        return cls(
            requests=[SearchRequestModel.from_search_request(r) for r in requests]
        )

    def model_dump_json(self, *args: Any, **kwargs: Any) -> Any:
        """
        Ensure that the model is called with `.model_dump_json(by_alias=True)`

        Setting `serialization_alias` requires the model to be called with `.model_dump(by_alias=True)`, but
        we do not want to leave this up to the caller.
        """
        kwargs["by_alias"] = True
        return super().model_dump_json(*args, **kwargs)


SearchResultDeserializer = RootModel[list[list[SearchResult]]]
