from typing import TypeVar, Generic, Union, Optional, Protocol, Tuple, List, Any, Self
from types import TracebackType
from enum import Flag, Enum, auto
from dataclasses import dataclass
from abc import abstractmethod
import weakref

from ..types import Result, Ok, Err, Some
from ..exports import skill_handler
from ..imports import streaming_output

class SkillHandler(Protocol):

    @abstractmethod
    def run(self, input: bytes) -> bytes:
        """
        Raises: `bindings.types.Err(bindings.imports.skill_handler.Error)`
        """
        raise NotImplementedError

    @abstractmethod
    def metadata(self) -> skill_handler.SkillMetadata:
        raise NotImplementedError


class MessageStream(Protocol):

    @abstractmethod
    def run(self, input: bytes, output: streaming_output.StreamOutput) -> None:
        """
        Run the skill. Output is streamed out of the stream-output resource.
        The skill is allowed to also terminate early with an error.
        
        Raises: `bindings.types.Err(bindings.imports.message_stream.Error)`
        """
        raise NotImplementedError


