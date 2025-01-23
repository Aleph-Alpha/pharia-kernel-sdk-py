"""
A WASI interface dedicated to interacting with Large Language Models and other AI-related tasks.
"""
from typing import TypeVar, Generic, Union, Optional, Protocol, Tuple, List, Any, Self
from types import TracebackType
from enum import Flag, Enum, auto
from dataclasses import dataclass
from abc import abstractmethod
import weakref

from ..types import Result, Ok, Err, Some


class FinishReason(Enum):
    """
    The reason the model finished generating
    """
    STOP = 0
    LENGTH = 1
    CONTENT_FILTER = 2

@dataclass
class Completion:
    """
    The result of a completion, including the text generated as well as
    why the model finished completing.
    """
    text: str
    finish_reason: FinishReason

@dataclass
class CompletionParams:
    """
    Completion request parameters
    """
    max_tokens: Optional[int]
    temperature: Optional[float]
    top_k: Optional[int]
    top_p: Optional[float]
    stop: List[str]

class Role(Enum):
    USER = 0
    ASSISTANT = 1
    SYSTEM = 2

@dataclass
class Message:
    role: Role
    content: str

@dataclass
class ChatParams:
    max_tokens: Optional[int]
    temperature: Optional[float]
    top_p: Optional[float]

@dataclass
class ChatResponse:
    """
    The result of a chat response, including the message generated as well as
    why the model finished completing.
    """
    message: Message
    finish_reason: FinishReason

@dataclass
class ChunkParams:
    """
    Chunking parameters
    """
    model: str
    max_tokens: int

class Language(Enum):
    """
    ISO 639-3
    """
    ENG = 0
    DEU = 1

@dataclass
class CompletionRequest:
    """
    Completion request parameters
    """
    model: str
    prompt: str
    params: CompletionParams

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
class SearchResult:
    document_path: DocumentPath
    content: str
    score: float


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


def complete(model: str, prompt: str, params: CompletionParams) -> Completion:
    raise NotImplementedError

def chat(model: str, messages: List[Message], params: ChatParams) -> ChatResponse:
    raise NotImplementedError

def chunk(text: str, params: ChunkParams) -> List[str]:
    raise NotImplementedError

def select_language(text: str, languages: List[Language]) -> Optional[Language]:
    """
    Select the detected language for the provided input based on the list of possible languages.
    If no language matches, None is returned.
    
    text: Text input
    languages: All languages that should be considered during detection.
    """
    raise NotImplementedError

def complete_all(requests: List[CompletionRequest]) -> List[Completion]:
    raise NotImplementedError

def search(index_path: IndexPath, query: str, max_results: int, min_score: Optional[float]) -> List[SearchResult]:
    raise NotImplementedError

def complete_return_special_tokens(model: str, prompt: str, params: CompletionParams) -> Completion:
    raise NotImplementedError

def document_metadata(document_path: DocumentPath) -> Optional[bytes]:
    raise NotImplementedError

def documents(requests: List[DocumentPath]) -> List[Document]:
    raise NotImplementedError

