"""
The tool interface allows Skills to interact with the outside world.
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


@dataclass
class Tool:
    name: str
    description: str
    input_schema: bytes


def invoke_tool(request: List[InvokeRequest]) -> List[Result[List[Modality], str]]:
    raise NotImplementedError

def list_tools() -> List[Tool]:
    """
    As long as we do not support tool calling in the inference, the prompt synthesis happens in the Skill code.
    It could also happen in the Kernel, but we already have the logic in the SDK, and it seems like this will
    move to inference soon anyway. Therefore, the Skill needs to know about the schema of the different tools.
    While this could be achieved by querying for a list of tool names, and then getting a list of options in
    the same order, simply listing all tools seems to be the simpler solution.
    """
    raise NotImplementedError

