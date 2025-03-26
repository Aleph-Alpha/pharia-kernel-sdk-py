"""
For some reason cannot enable unstable here
@unstable(feature = streaming)
"""
from typing import TypeVar, Generic, Union, Optional, Protocol, Tuple, List, Any, Self
from types import TracebackType
from enum import Flag, Enum, auto
from dataclasses import dataclass
from abc import abstractmethod
import weakref

from ..types import Result, Ok, Err, Some



@dataclass
class Error_Internal:
    value: str


@dataclass
class Error_InvalidInput:
    value: str


Error = Union[Error_Internal, Error_InvalidInput]
"""
The set of errors which may be raised by functions in this interface
"""


