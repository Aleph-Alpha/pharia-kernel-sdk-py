from typing import TypeVar, Generic, Union, Optional, Protocol, Tuple, List, Any, Self
from types import TracebackType
from enum import Flag, Enum, auto
from dataclasses import dataclass
from abc import abstractmethod
import weakref

from ..types import Result, Ok, Err, Some


@dataclass
class TextScore:
    """
    A score for a text segment.
    """
    start: int
    length: int
    score: float

class Granularity(Enum):
    """
    At which granularity should the target be explained in terms of the prompt.
    If you choose, for example, [`granularity.sentence`] then we report the importance score of each
    sentence in the prompt towards generating the target output.
    The default is [`granularity.auto`] which means we will try to find the granularity that
    brings you closest to around 30 explanations. For large prompts, this would likely
    be sentences. For short prompts this might be individual words or even tokens.
    """
    AUTO = 0
    WORD = 1
    SENTENCE = 2
    PARAGRAPH = 3

@dataclass
class ExplanationRequest:
    prompt: str
    target: str
    model: str
    granularity: Granularity

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


def explain(request: List[ExplanationRequest]) -> List[List[TextScore]]:
    """
    Better understand the source of a completion, specifically on how much each section of a prompt impacts each token of the completion.
    """
    raise NotImplementedError

def complete(requests: List[CompletionRequest]) -> List[Completion]:
    raise NotImplementedError

def chat(requests: List[ChatRequest]) -> List[ChatResponse]:
    raise NotImplementedError

