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
    TOOL_CALLS = 3

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
    echo: bool

@dataclass
class CompletionRequest:
    """
    Completion request parameters
    """
    model: str
    prompt: str
    params: CompletionParams

@dataclass
class CompletionAppend:
    """
    A chunk of a completion returned by a completion stream.
    """
    text: str
    logprobs: List[Distribution]


@dataclass
class CompletionEvent_Append:
    value: CompletionAppend


@dataclass
class CompletionEvent_End:
    value: FinishReason


@dataclass
class CompletionEvent_Usage:
    value: TokenUsage


CompletionEvent = Union[CompletionEvent_Append, CompletionEvent_End, CompletionEvent_Usage]
"""
An event emitted by a completion stream.
"""


class CompletionStream:
    """
    Allows for streaming completion tokens as they are generated.
    """
    
    def __init__(self, init: CompletionRequest) -> None:
        """
        Creates a new completion-stream resource for a given completion-request.
        """
        raise NotImplementedError

    def next(self) -> Optional[CompletionEvent]:
        """
        Returns the next completion-event from the completion-stream.
        Will return None if the stream has finished.
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


@dataclass
class ToolMessage:
    content: str
    tool_call_id: str

@dataclass
class OtherMessage:
    role: str
    content: str

@dataclass
class ToolCall:
    """
    A tool call as requested by the model.
    """
    id: str
    name: str
    arguments: str

@dataclass
class AssistantMessage:
    content: Optional[str]
    tool_calls: Optional[List[ToolCall]]


@dataclass
class Message_Assistant:
    value: AssistantMessage


@dataclass
class Message_Tool:
    value: ToolMessage


@dataclass
class Message_Other:
    value: OtherMessage


Message = Union[Message_Assistant, Message_Tool, Message_Other]


@dataclass
class Function:
    name: str
    description: Optional[str]
    parameters: Optional[bytes]
    strict: Optional[bool]


@dataclass
class ToolChoice_None_:
    pass


@dataclass
class ToolChoice_Auto:
    pass


@dataclass
class ToolChoice_Required:
    pass


@dataclass
class ToolChoice_Named:
    value: str


ToolChoice = Union[ToolChoice_None_, ToolChoice_Auto, ToolChoice_Required, ToolChoice_Named]


class ReasoningEffort(Enum):
    MINIMAL = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3

@dataclass
class JsonSchema:
    description: Optional[str]
    name: str
    schema: Optional[bytes]
    strict: Optional[bool]


@dataclass
class ResponseFormat_Text:
    pass


@dataclass
class ResponseFormat_JsonObject:
    pass


@dataclass
class ResponseFormat_JsonSchema:
    value: JsonSchema


ResponseFormat = Union[ResponseFormat_Text, ResponseFormat_JsonObject, ResponseFormat_JsonSchema]


@dataclass
class ChatParams:
    max_tokens: Optional[int]
    max_completion_tokens: Optional[int]
    temperature: Optional[float]
    top_p: Optional[float]
    frequency_penalty: Optional[float]
    presence_penalty: Optional[float]
    logprobs: Logprobs
    tools: Optional[List[Function]]
    tool_choice: Optional[ToolChoice]
    parallel_tool_calls: Optional[bool]
    response_format: Optional[ResponseFormat]
    reasoning_effort: Optional[ReasoningEffort]

@dataclass
class ChatResponse:
    """
    The result of a chat response, including the message generated as well as
    why the model finished completing.
    """
    message: AssistantMessage
    finish_reason: FinishReason
    logprobs: List[Distribution]
    usage: TokenUsage

@dataclass
class ChatRequest:
    model: str
    messages: List[Message]
    params: ChatParams

@dataclass
class MessageAppend:
    """
    A chunk of a message generated by the model.
    """
    content: str
    logprobs: List[Distribution]

@dataclass
class ToolCallChunk:
    index: int
    id: Optional[str]
    name: Optional[str]
    arguments: Optional[str]


@dataclass
class ChatEvent_MessageBegin:
    value: str


@dataclass
class ChatEvent_MessageAppend:
    value: MessageAppend


@dataclass
class ChatEvent_MessageEnd:
    value: FinishReason


@dataclass
class ChatEvent_Usage:
    value: TokenUsage


@dataclass
class ChatEvent_ToolCall:
    value: List[ToolCallChunk]


ChatEvent = Union[ChatEvent_MessageBegin, ChatEvent_MessageAppend, ChatEvent_MessageEnd, ChatEvent_Usage, ChatEvent_ToolCall]
"""
An event emitted by the chat-stream resource.
"""


class ChatStream:
    
    def __init__(self, init: ChatRequest) -> None:
        """
        Creates a new chat-stream resource for a given chat-request.
        """
        raise NotImplementedError

    def next(self) -> Optional[ChatEvent]:
        """
        Returns the next chat-event from the chat-stream.
        Will return None if the stream has finished.
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



def complete(requests: List[CompletionRequest]) -> List[Completion]:
    raise NotImplementedError

def chat(requests: List[ChatRequest]) -> List[ChatResponse]:
    raise NotImplementedError

