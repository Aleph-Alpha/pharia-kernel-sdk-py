from typing import TypeVar, Generic, Union, Optional, Protocol, Tuple, List, Any, Self
from types import TracebackType
from enum import Flag, Enum, auto
from dataclasses import dataclass
from abc import abstractmethod
import weakref

from ..types import Result, Ok, Err, Some


@dataclass
class ChunkParams:
    """
    Chunking parameters
    """
    model: str
    max_tokens: int
    overlap: int

@dataclass
class ChunkRequest:
    text: str
    params: ChunkParams


def chunk(request: List[ChunkRequest]) -> List[List[str]]:
    raise NotImplementedError

