"""
A WASI interface dedicated to interacting with Large Language Models and other AI-related tasks.
"""
from typing import TypeVar, Generic, Union, Optional, Protocol, Tuple, List, Any, Self
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


def complete(model: str, prompt: str, params: CompletionParams) -> Completion:
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

