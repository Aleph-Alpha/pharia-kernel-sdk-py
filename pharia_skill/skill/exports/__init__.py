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
        Raises: `skill.types.Err(skill.imports.skill_handler.Error)`
        """
        raise NotImplementedError


