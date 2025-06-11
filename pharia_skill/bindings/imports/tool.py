"""
The tool interface allows Skills to interact with the outside world.
We run into issues making the interface itself unstable, so only
all members are marked as unstable.
"""
from typing import TypeVar, Generic, Union, Optional, Protocol, Tuple, List, Any, Self
from types import TracebackType
from enum import Flag, Enum, auto
from dataclasses import dataclass
from abc import abstractmethod
import weakref

from ..types import Result, Ok, Err, Some


@dataclass
class Argument:
    name: str
    value: bytes

@dataclass
class InvokeRequest:
    tool_name: str
    arguments: List[Argument]


@dataclass
class Modality_Text:
    value: str


Modality = Union[Modality_Text]



def invoke_tool(request: List[InvokeRequest]) -> List[List[Modality]]:
    raise NotImplementedError

