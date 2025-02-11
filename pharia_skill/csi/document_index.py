import datetime as dt
from dataclasses import dataclass, field
from typing import Any, Literal, Sequence


@dataclass
class DocumentPath:
    """Path identifying a document.

    A DocumentPath consists of a namespace, within the namespace a collection and within the collection a document has a name.

    Attributes:
        namespace (str): The namespace.
        collection (str): The collection within the namespace.
        name (str): The name identifying the document in the collection.
    """

    namespace: str
    collection: str
    name: str


@dataclass
class IndexPath:
    """Which documents you want to search in, and which type of index should be used.

    Attributes:
        namespace (string): The namespace the collection belongs to.
        collection (string): The collection you want to search in.
        index (str): The search index you want to use for the collection.
    """

    namespace: str
    collection: str
    index: str


@dataclass
class GreaterThan:
    value: float


@dataclass
class GreaterThanOrEqualTo:
    value: float


@dataclass
class LessThan:
    value: float


@dataclass
class LessThanOrEqualTo:
    value: float


@dataclass
class After:
    value: dt.datetime


@dataclass
class AtOrAfter:
    value: dt.datetime


@dataclass
class Before:
    value: dt.datetime


@dataclass
class AtOrBefore:
    value: dt.datetime


@dataclass
class EqualTo:
    value: str | int | bool


@dataclass
class IsNull:
    """This condition matches all metadata fields with a value of null."""

    pass


FilterCondition = (
    GreaterThan
    | GreaterThanOrEqualTo
    | LessThan
    | LessThanOrEqualTo
    | After
    | AtOrAfter
    | Before
    | AtOrBefore
    | EqualTo
    | IsNull
)


@dataclass
class MetadataFilter:
    """Matches sections whose metadata fields match the given condition. You must specify the field, and can only specify a single condition.

    While the Document Index also offers a `Modality` filter, we do not expose this to the developer.
    The reasoning is that we only allow for text modalities in the Kernel. So for each search request,
    we append a `Modality` filter that only allows for text modalities.

    Attributes:
        field (str): The metadata field on which to filter search results.
            Field names must only contain alphanumeric characters, dashes and underscores.
            Nested fields can be specified using dot notation (e.g. 'a.b').
            Array-valued fields can either use a wildcard specifier (e.g. 'a[].b') or a specific index (e.g. 'a[1].b').
            The maximum length of the field name is 1000 characters.
        condition (FilterCondition): The condition to filter on.
    """

    field: str
    condition: FilterCondition


@dataclass
class Without:
    """Logical conjunction of negations, i.e. forms the predicate "(NOT filterCondition1) AND (NOT filterCondition2) AND ..."

    Attributes:
        value (list[Filter]): The list of filter conditions.
    """

    value: list[MetadataFilter]


@dataclass
class WithOneOf:
    """Logical disjunction, i.e. forms the predicate "filterCondition1 OR filterCondition2 OR ..."

    Attributes:
        value (list[Filter]): The list of filter conditions.
    """

    value: list[MetadataFilter]


@dataclass
class WithAll:
    """Logical conjunction, i.e. forms the predicate "filterCondition1 AND filterCondition2 AND ..."

    Attributes:
        value (list[Filter]): The list of filter conditions.
    """

    value: list[MetadataFilter]


SearchFilter = Without | WithOneOf | WithAll
"""A logical combination of filter conditions."""


@dataclass
class SearchRequest:
    """A request to search the document index.

    Attributes:
        index_path (IndexPath): The index path to search in.
        query (str): The query to search for.
        max_results (int): Maximum number of results to return. Defaults to 1.
        min_score (float | None): Filter out results with a cosine similarity score below this value.
            Scores range from -1 to 1. For searches on hybrid indexes, the Document Index applies the min_score to the semantic results before fusion of result sets.
            As fusion re-scores results, returned scores may exceed this value.
        filters (list[SearchFilter]): A filter for search results that restricts the results to those document sections that match the filter criteria.
            The individual conditions of this array are AND-combined (i.e. all conditions must match).
            This can for example be used to restrict the returned sections based on their modality (i.e. image or text), or on their metadata.
    """

    index_path: IndexPath
    query: str
    max_results: int = 1
    min_score: float | None = None
    filters: Sequence[SearchFilter] = field(default_factory=list)


@dataclass
class Cursor:
    """A position within a document.

    The cursor is always inclusive of the current position, in both start and end positions.

    Attributes:
        item (int): Index of the item in the document. A document is an array of text and image elements. These elements are referred to as items.
        position (int): The character position the cursor can be found at within the string.
    """

    item: int
    position: int


@dataclass
class SearchResult:
    """The relevant documents as result of a search request.

    Attributes:
        document_path (DocumentPath): The path to a document. A path uniquely identifies a document among all managed documents.
        content (str): The text of the found section. As we do not support multi-modal, this is always a string.
        score (float): Search score of the found section, where a higher score indicates a closer match.
            Will be between -1 and 1. A score closer to -1 indicates the section opposes the query.
            A score close 0 suggests the section is unrelated to the query.
            A score close to 1 suggests the section is related to the query.
        start (Cursor): Where the result starts in the document.
        end (Cursor): Where the result ends in the document.
    """

    document_path: DocumentPath
    content: str
    score: float
    start: Cursor
    end: Cursor


@dataclass
class Text:
    """A text section that is part of a document.

    If the document only contains text, then the contents of the document is a list of
    length one, where the only element is a `Text`."""

    text: str
    modality: Literal["text"] = "text"


@dataclass
class Image:
    """An image that is part of a document.

    At the moment, we do not expose the image contents, as none of the models
    support multi-modal inputs. We still inform the developer that the document
    contains an image.
    """

    modality: Literal["image"] = "image"


Modality = Text | Image
"""A document is made up of subsections of different modalities.

For example, if a document is a long text with an image in the middle, then
it will be represented by a list of length three, where the first and last
elements are `Text` and the middle element is `Image`.
"""


JsonSerializable = dict[str, Any] | list[Any] | str | int | float | bool | None
"""Represent any value that can be serialized/deserialized to/from JSON.

Used to represent the return type of `document_metadata` which is any valid JSON value.
"""


@dataclass
class Document:
    """A document in the Document Index.

    Attributes:
        path (DocumentPath): The path that identifies the document.
        contents (list[Modality]): The contents of the document. Split into sections of different modalities.
        metadata (JsonSerializable): The (custom) metadata of the document.
    """

    path: DocumentPath
    contents: list[Modality]
    metadata: JsonSerializable

    @property
    def text(self) -> str:
        """Concatenate the text contents of the document."""
        return "\n\n".join(
            text.text for text in self.contents if isinstance(text, Text)
        )
