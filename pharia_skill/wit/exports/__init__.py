from typing import TypeVar, Generic, Union, Optional, Protocol, Tuple, List, Any, Self
from enum import Flag, Enum, auto
from dataclasses import dataclass
from abc import abstractmethod
import weakref

from ..types import Result, Ok, Err, Some


class SkillHandler(Protocol):

    @abstractmethod
    def run(self, input: bytes) -> bytes:
        """
        Raises: `wit.types.Err(wit.imports.skill_handler.Error)`
        """
        raise NotImplementedError


