from typing import TypeVar, Generic, Union, Optional, Protocol, Tuple, List, Any, Self
from types import TracebackType
from enum import Flag, Enum, auto
from dataclasses import dataclass
from abc import abstractmethod
import weakref

from ..types import Result, Ok, Err, Some


@dataclass
class IndexPath:
    """
    Which documents you want to search in, and which type of index should be used
    """
    namespace: str
    collection: str
    index: str

@dataclass
class DocumentPath:
    namespace: str
    collection: str
    name: str

@dataclass
class TextCursor:
    item: int
    position: int

@dataclass
class SearchResult:
    document_path: DocumentPath
    content: str
    score: float
    start: TextCursor
    end: TextCursor


@dataclass
class MetadataFieldValue_StringType:
    value: str


@dataclass
class MetadataFieldValue_IntegerType:
    value: int


@dataclass
class MetadataFieldValue_BooleanType:
    value: bool


MetadataFieldValue = Union[MetadataFieldValue_StringType, MetadataFieldValue_IntegerType, MetadataFieldValue_BooleanType]



@dataclass
class MetadataFilterCondition_GreaterThan:
    value: float


@dataclass
class MetadataFilterCondition_GreaterThanOrEqualTo:
    value: float


@dataclass
class MetadataFilterCondition_LessThan:
    value: float


@dataclass
class MetadataFilterCondition_LessThanOrEqualTo:
    value: float


@dataclass
class MetadataFilterCondition_After:
    value: str


@dataclass
class MetadataFilterCondition_AtOrAfter:
    value: str


@dataclass
class MetadataFilterCondition_Before:
    value: str


@dataclass
class MetadataFilterCondition_AtOrBefore:
    value: str


@dataclass
class MetadataFilterCondition_EqualTo:
    value: MetadataFieldValue


@dataclass
class MetadataFilterCondition_IsNull:
    pass


MetadataFilterCondition = Union[MetadataFilterCondition_GreaterThan, MetadataFilterCondition_GreaterThanOrEqualTo, MetadataFilterCondition_LessThan, MetadataFilterCondition_LessThanOrEqualTo, MetadataFilterCondition_After, MetadataFilterCondition_AtOrAfter, MetadataFilterCondition_Before, MetadataFilterCondition_AtOrBefore, MetadataFilterCondition_EqualTo, MetadataFilterCondition_IsNull]


@dataclass
class MetadataFilter:
    field: str
    condition: MetadataFilterCondition


@dataclass
class SearchFilter_Without:
    value: List[MetadataFilter]


@dataclass
class SearchFilter_WithOneOf:
    value: List[MetadataFilter]


@dataclass
class SearchFilter_WithAll:
    value: List[MetadataFilter]


SearchFilter = Union[SearchFilter_Without, SearchFilter_WithOneOf, SearchFilter_WithAll]


@dataclass
class SearchRequest:
    index_path: IndexPath
    query: str
    max_results: int
    min_score: Optional[float]
    filters: List[SearchFilter]


@dataclass
class Modality_Text:
    value: str


@dataclass
class Modality_Image:
    pass


Modality = Union[Modality_Text, Modality_Image]


@dataclass
class Document:
    path: DocumentPath
    contents: List[Modality]
    metadata: Optional[bytes]


def search(requests: List[SearchRequest]) -> List[List[SearchResult]]:
    raise NotImplementedError

def document_metadata(requests: List[DocumentPath]) -> List[Optional[bytes]]:
    raise NotImplementedError

def documents(requests: List[DocumentPath]) -> List[Document]:
    raise NotImplementedError

