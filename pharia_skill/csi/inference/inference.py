"""
This module exposes the interfaces for skills to interact with the Pharia Kernel
via the Cognitive System Interface (CSI).
"""

from abc import ABC, abstractmethod
from collections import deque
from collections.abc import Generator
from dataclasses import field
from enum import Enum
from types import TracebackType
from typing import Any, Literal, Self

# We use pydantic.dataclasses to get type validation.
# See the docstring of `csi` module for more information on the why.
from pydantic.dataclasses import dataclass

from pharia_skill.csi.inference.tool import ToolCallRequest, parse_tool_call

from .types import (
    ChatEvent,
    Distribution,
    FinishReason,
    Message,
    MessageAppend,
    MessageBegin,
    TokenUsage,
)


@dataclass
class TopLogprobs:
    """Request between 0 and 20 tokens"""

    top: int


NoLogprobs = Literal["no"]
"""Do not return any logprobs"""


SampledLogprobs = Literal["sampled"]
"""Return only the logprob of the tokens which have actually been sampled into the completion."""


Logprobs = TopLogprobs | NoLogprobs | SampledLogprobs
"""Control the logarithmic probabilities you want to have returned."""


@dataclass
class CompletionParams:
    """Completion request parameters.

    Attributes:
        max-tokens (int, optional, default None): The maximum tokens that should be inferred. Note, the backing implementation may return less tokens due to other stop reasons.
        temperature (float, optional, default None): The randomness with which the next token is selected.
        top-k (int, optional, default None): The number of possible next tokens the model will choose from.
        top-p (float, optional, default None): The probability total of next tokens the model will choose from.
        stop (list(str), optional, default []): A list of sequences that, if encountered, the API will stop generating further tokens.
        return_special_tokens (bool, optional, default True): Whether to include special tokens (e.g. <|endoftext|>, <|python_tag|>) in the completion response.
        frequency-penalty (float, optional, default None): The presence penalty reduces the probability of generating tokens that are already present in the generated text respectively prompt. Presence penalty is independent of the number of occurrences. Increase the value to reduce the probability of repeating text.
        presence-penalty (float, optional, default None): The presence penalty reduces the probability of generating tokens that are already present in the generated text respectively prompt. Presence penalty is independent of the number of occurrences. Increase the value to reduce the probability of repeating text.
        logprobs (Logprobs, optional, default NoLogprobs()): Use this to control the logarithmic probabilities you want to have returned. This is useful to figure out how likely it had been that this specific token had been sampled.
        echo (bool, optional, default False): Whether to include the prompt in the completion response. This parameter is not supported for streaming requests.
    """

    max_tokens: int | None = None
    temperature: float | None = None
    top_k: int | None = None
    top_p: float | None = None
    stop: list[str] = field(default_factory=list)

    # While the default of this parameters in the api-scheduler is False, we believe that
    # with the introduction of the chat endpoint, the completion endpoint is mostly used for
    # queries where the average user is interested in theses tokens.
    return_special_tokens: bool = True
    frequency_penalty: float | None = None
    presence_penalty: float | None = None
    logprobs: Logprobs = "no"
    echo: bool = False


@dataclass
class CompletionAppend:
    """A chunk of a completion returned by a completion stream.

    Attributes:
        text (str, required): A chunk of the completion text.
        logprobs (list[Distribution], required): Corresponding log probabilities for each token in the completion.
    """

    text: str
    logprobs: list[Distribution]

    @classmethod
    def from_dict(cls, body: dict[str, Any]) -> "CompletionAppend":
        return cls(
            text=body["text"],
            logprobs=body["logprobs"],
        )


CompletionEvent = CompletionAppend | FinishReason | TokenUsage


class CompletionStreamResponse(ABC):
    """Abstract base class for streaming completion responses.

    This class provides the core functionality for streaming completion from a model.
    Concrete implementations only need to implement the `next()` method to provide
    the next event in the stream, and optionally override `__enter__` and `__exit__`
    methods for proper resource management.

    The `__enter__` and `__exit__` methods are particularly important for implementations
    that need to manage external resources. For example, in the `WitCsi` implementation,
    these methods ensure that resources are properly released when the stream is no longer
    needed.
    """

    _finish_reason: FinishReason | None = None
    _usage: TokenUsage | None = None

    def __enter__(self) -> Self:
        """Enter the context manager."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        """Exit the context manager and ensure resources are properly cleaned up."""
        pass

    @abstractmethod
    def next(self) -> CompletionEvent | None:
        """Get the next completion event."""
        ...

    def finish_reason(self) -> FinishReason:
        """The reason the model finished generating."""

        if self._usage is None:
            self._consume_stream()
        assert self._finish_reason is not None
        return self._finish_reason

    def usage(self) -> TokenUsage:
        """Usage statistics for the completion request."""

        if self._usage is None:
            self._consume_stream()
        assert self._usage is not None
        return self._usage

    def _consume_stream(self) -> None:
        deque(self.stream(), maxlen=0)
        if self._finish_reason is None or self._usage is None:
            raise ValueError("Invalid event stream")

    def stream(self) -> Generator[CompletionAppend, None, None]:
        """Stream completion chunks."""

        if self._usage:
            raise RuntimeError("The stream has already been consumed")
        while (event := self.next()) is not None:
            match event:
                case CompletionAppend():
                    yield event
                case FinishReason():
                    self._finish_reason = event
                case TokenUsage():
                    self._usage = event
                case _:
                    raise ValueError("Invalid event")


class ChatStreamResponse(ABC):
    """Abstract base class for streaming chat responses.

    This class provides the core functionality for streaming chat from a model.
    Concrete implementations only need to implement the `next()` method to provide
    the next event in the stream, and optionally override `__enter__` and `__exit__`
    methods for proper resource management.

    The `__enter__` and `__exit__` methods are particularly important for implementations
    that need to manage external resources. For example, in the `WitCsi` implementation,
    these methods ensure that resources are properly released when the stream is no longer
    needed.

    The content of the message can be streamed by calling `stream()`.
    If `finish_reason()` or `usage()` has been called, the stream is consumed.


    Attributes:
        role (str, required): The role of the message.
    """

    role: str
    buffer: list[ChatEvent]

    _finish_reason: FinishReason | None = None
    _usage: TokenUsage | None = None
    _tool_call: ToolCallRequest | None = None

    def __enter__(self) -> Self:
        """Enter the context manager."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        """Exit the context manager and ensure resources are properly cleaned up."""
        pass

    def next(self) -> ChatEvent | None:
        """Get the next chat event.

        If there are events stored in the internal buffer, use them as event source.
        Otherwise, get the next event from the stream. Keeping track of events in the
        buffer allows others to peek at the next stream event without altering the
        stream. An example where this is necessary is when checking for a tool call.
        """
        if self.buffer:
            return self.buffer.pop(0)
        else:
            return self._next()

    @abstractmethod
    def _next(self) -> ChatEvent | None:
        """Get the next chat event from the stream."""
        ...

    def _peek(self) -> ChatEvent | None:
        """Peek at the next chat event without changing the stream."""
        event = self._next()
        if event is not None:
            self.buffer.append(event)
        return event

    def _peek_iterator(self) -> Generator[ChatEvent, None, None]:
        """An iterator over the chat events that does not alter the stream."""
        while (event := self._peek()) is not None:
            yield event

    def __init__(self) -> None:
        self.buffer = []
        first_event = self._next()
        if not isinstance(first_event, MessageBegin):
            raise ValueError(f"Invalid first stream event: {first_event}")
        self.role = first_event.role

    def tool_call(self) -> ToolCallRequest | None:
        """Inspect the stream to find out if the model is calling a tool.

        This method must be called before the stream is consumed. A typical usage
        pattern would be to check for the tool call, and, if there is none, stream the
        rest of the message. In case the response is not a tool call, normally only
        one element of the stream needs to be inspected, so the impact is minimal.
        However, in edge scenarios, the full stream might need to be inspected.

        Returns:
            The tool call if there is one in the request, otherwise `None`.

        Example::

            response = csi.chat_stream("llama-3.1-8b-instruct", [system, user], params)
            tool_call = response.tool_call()
            if tool_call:
                # Handle the tool call
            else:
                writer.forward_response(response)
        """
        if self._tool_call is None:
            self._tool_call = parse_tool_call(self._peek_iterator())

        return self._tool_call

    def finish_reason(self) -> FinishReason:
        """The reason the model finished generating."""

        if self._usage is None:
            self._consume_stream()
        assert self._finish_reason is not None
        return self._finish_reason

    def usage(self) -> TokenUsage:
        """Usage statistics for the chat request."""

        if self._usage is None:
            self._consume_stream()
        assert self._usage is not None
        return self._usage

    def _consume_stream(self) -> None:
        deque(self.stream(), maxlen=0)
        if self._finish_reason is None or self._usage is None:
            raise ValueError("Invalid event stream")

    def stream(self) -> Generator[MessageAppend, None, None]:
        """Stream the content of the message.

        This does not include the role, the finish reason and usage.
        """
        if self._usage:
            raise RuntimeError("The stream has already been consumed")
        while (event := self.next()) is not None:
            match event:
                case MessageBegin():
                    raise ValueError("Invalid event stream")
                case MessageAppend():
                    yield event
                case FinishReason():
                    self._finish_reason = event
                case TokenUsage():
                    self._usage = event
                    break


@dataclass
class Completion:
    """The result of a completion, including the text generated as well as
    why the model finished completing.

    Attributes:
        text (str, required): The text generated by the model.
        finish-reason (FinishReason, required): The reason the model finished generating.
        logprobs (list[Distribution], required): Contains the logprobs for the sampled and top n tokens, given that `completion-request.params.logprobs` has been set to `sampled` or `top`.
        usage (TokenUsage, required): Usage statistics for the completion request.
    """

    text: str
    finish_reason: FinishReason
    logprobs: list[Distribution]
    usage: TokenUsage

    @classmethod
    def from_dict(cls, body: dict[str, Any]) -> "Completion":
        finish_reason = FinishReason(body["finish_reason"])
        return cls(
            text=body["text"],
            finish_reason=finish_reason,
            logprobs=body["logprobs"],
            usage=body["usage"],
        )


@dataclass
class CompletionRequest:
    """Request a completion from the model

    Attributes:
        model (str, required): Name of model to use.
        prompt (str, required): The text to be completed.
        params (CompletionParams, optional, Default CompletionParams()):
            Parameters for the requested completion.
    """

    model: str
    prompt: str
    params: CompletionParams = field(default_factory=CompletionParams)


@dataclass
class ChatParams:
    """Chat request parameters.

    Attributes:
        max-tokens (int, optional, default None):  The maximum tokens that should be inferred. Note, the backing implementation may return less tokens due to other stop reasons.
        temperature (float, optional, default None): The randomness with which the next token is selected.
        top-p (float, optional, default None): The probability total of next tokens the model will choose from.
        frequency-penalty (float, optional, default None): The presence penalty reduces the probability of generating tokens that are already present in the generated text respectively prompt. Presence penalty is independent of the number of occurrences. Increase the value to reduce the probability of repeating text.
        presence-penalty (float, optional, default None): The presence penalty reduces the probability of generating tokens that are already present in the generated text respectively prompt. Presence penalty is independent of the number of occurrences. Increase the value to reduce the probability of repeating text.
        logprobs (Logprobs, optional, default NoLogprobs()): Use this to control the logarithmic probabilities you want to have returned. This is useful to figure out how likely it had been that this specific token had been sampled.
    """

    max_tokens: int | None = None
    temperature: float | None = None
    top_p: float | None = None
    frequency_penalty: float | None = None
    presence_penalty: float | None = None
    logprobs: Logprobs = "no"


@dataclass
class ChatRequest:
    """A request for a model to generate a response from a conversation.

    Only one optional "system" message is allowed at the beginning of the conversation.
    The remaining conversation must alternate between "user" and "assistant" messages,
    and must begin with a "user" message.

    Attributes:
        model (str, required): Name of model to use.
        messages (list[Message], required): A list of messages comprising the
            conversation so far.
        params (ChatParams, optional, Default ChatParams()):
            Parameters for the requested chat.
    """

    model: str
    messages: list[Message]
    params: ChatParams = field(default_factory=ChatParams)


@dataclass
class ChatResponse:
    """The result of a chat request.

    Attributes:
        message (Message): The generated message.
        finish_reason (FinishReason): Why the model finished completing.
        logprobs (list[Distribution]): Contains the logprobs for the sampled and top n tokens, given that `chat-request.params.logprobs` has been set to `sampled` or `top`.
        usage (TokenUsage): Usage statistics for the chat request.
    """

    message: Message
    finish_reason: FinishReason
    logprobs: list[Distribution]
    usage: TokenUsage

    @staticmethod
    def from_dict(body: dict[str, Any]) -> "ChatResponse":
        message = Message.from_dict(body["message"])
        finish_reason = FinishReason(body["finish_reason"])
        logprobs = [Distribution.from_dict(logprob) for logprob in body["logprobs"]]
        usage = TokenUsage(body["usage"]["prompt"], body["usage"]["completion"])
        return ChatResponse(message, finish_reason, logprobs, usage)


@dataclass
class TextScore:
    """A range of text with a score indicating how much it influenced the completion.

    Attributes:
        start (int): The start index of the text segment w.r.t. to characters in the prompt.
        length (int): Length of the text segment w.r.t. to characters in the prompt.
        score (float): The score of the text segment, higher means more relevant.
    """

    start: int
    length: int
    score: float


class Granularity(str, Enum):
    """The granularity of the explanation."""

    AUTO = "auto"
    WORD = "word"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"


@dataclass
class ExplanationRequest:
    """Request an explanation for the completion.

    Attributes:
        prompt (str): The prompt used for the completion.
        target (str): The completion text.
        model (str): The model used for the completion.
        granularity (Granularity, optional, Default Granularity.AUTO):
            Controls the length of the ranges which are explained.
    """

    prompt: str
    target: str
    model: str
    granularity: Granularity = Granularity.AUTO
