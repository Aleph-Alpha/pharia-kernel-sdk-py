from typing import TypeVar, Generic, Union, Optional, Protocol, Tuple, List, Any, Self
from types import TracebackType
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
class Logprob:
    token: bytes
    logprob: float

@dataclass
class Distribution:
    sampled: Logprob
    top: List[Logprob]

@dataclass
class TokenUsage:
    prompt: int
    completion: int

@dataclass
class Completion:
    """
    The result of a completion, including the text generated as well as
    why the model finished completing.
    """
    text: str
    finish_reason: FinishReason
    logprobs: List[Distribution]
    usage: TokenUsage


@dataclass
class Logprobs_No:
    pass


@dataclass
class Logprobs_Sampled:
    pass


@dataclass
class Logprobs_Top:
    value: int


Logprobs = Union[Logprobs_No, Logprobs_Sampled, Logprobs_Top]


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
    return_special_tokens: bool
    frequency_penalty: Optional[float]
    presence_penalty: Optional[float]
    logprobs: Logprobs

@dataclass
class CompletionRequest:
    """
    Completion request parameters
    """
    model: str
    prompt: str
    params: CompletionParams

@dataclass
class Message:
    role: str
    content: str

@dataclass
class ChatParams:
    max_tokens: Optional[int]
    temperature: Optional[float]
    top_p: Optional[float]
    frequency_penalty: Optional[float]
    presence_penalty: Optional[float]
    logprobs: Logprobs

@dataclass
class ChatResponse:
    """
    The result of a chat response, including the message generated as well as
    why the model finished completing.
    """
    message: Message
    finish_reason: FinishReason
    logprobs: List[Distribution]
    usage: TokenUsage

@dataclass
class ChatRequest:
    model: str
    messages: List[Message]
    params: ChatParams


def complete(requests: List[CompletionRequest]) -> List[Completion]:
    raise NotImplementedError

def chat(requests: List[ChatRequest]) -> List[ChatResponse]:
    raise NotImplementedError

