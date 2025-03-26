from typing import TypeVar, Generic, Union, Optional, Protocol, Tuple, List, Any, Self
from types import TracebackType
from enum import Flag, Enum, auto
from dataclasses import dataclass
from abc import abstractmethod
import weakref

from ..types import Result, Ok, Err, Some
from ..exports import skill_handler

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


