"""
Provided host types for supporting running streaming skills.
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
class BeginAttributes:
    """
    Payload for the beginning of a message.
    """
    role: Optional[str]


@dataclass
class MessageItem_MessageBegin:
    value: BeginAttributes


@dataclass
class MessageItem_MessageAppend:
    value: str


@dataclass
class MessageItem_MessageEnd:
    value: Optional[bytes]


MessageItem = Union[MessageItem_MessageBegin, MessageItem_MessageAppend, MessageItem_MessageEnd]
"""
For some reason cannot enable unstable here
@unstable(feature = streaming)
"""


class StreamOutput:
    
    def write(self, item: MessageItem) -> None:
        """
        Puts part of a message into the output stream.
        """
        raise NotImplementedError
    def __enter__(self) -> Self:
        """Returns self"""
        return self
                                
    def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None) -> bool | None:
        """
        Release this resource.
        """
        raise NotImplementedError



