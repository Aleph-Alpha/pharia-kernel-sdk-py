"""
This module exposes the interfaces for skills to interact with the Pharia Kernel
via the Cognitive System Interface (CSI).
"""

from abc import ABC, abstractmethod
from collections import deque
from collections.abc import Generator
from dataclasses import dataclass, field
from enum import Enum
from types import TracebackType
from typing import Any, Literal, Self

from pydantic import field_validator


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
    """

    max_tokens: int | None = None
    temperature: float | None = None
    top_k: int | None = None
    top_p: float | None = None
    stop: list[str] = field(default_factory=lambda: list())

    # While the default of this parameters in the api-scheduler is False, we believe that
    # with the introduction of the chat endpoint, the completion endpoint is mostly used for
    # queries where the average user is interested in theses tokens.
    return_special_tokens: bool = True
    frequency_penalty: float | None = None
    presence_penalty: float | None = None
    logprobs: Logprobs = "no"


class FinishReason(str, Enum):
    """The reason the model finished generating.

    Attributes:
        STOP: The model hit a natural stopping point or a provided stop sequence.

        LENGTH: The maximum number of tokens specified in the request was reached.

        CONTENT_FILTER: Content was omitted due to a flag from content filters.
    """

    STOP = "stop"
    LENGTH = "length"
    CONTENT_FILTER = "content_filter"


@dataclass
class Logprob:
    """Logarithmic probability of the token returned in the completion."""

    token: bytes
    logprob: float

    @field_validator("token", mode="before")
    @classmethod
    def convert_token_to_bytes(cls, v: Any) -> Any:
        if isinstance(v, list):
            return bytes(v)
        return v

    def try_as_utf8(self) -> str | None:
        """Try to decode the token as utf-8.

        A token may also represent just a part of an utf-8 character, in which
        case it does not have a valid utf-8 encoding on its own.
        """
        try:
            return self.token.decode("utf-8")
        except UnicodeDecodeError:
            return None


@dataclass
class Distribution:
    sampled: Logprob
    top: list[Logprob]

    @classmethod
    def from_dict(cls, body: dict[str, Any]) -> "Distribution":
        raise NotImplementedError(
            "Not implemented, maybe look into pydantic dataclasses"
        )


@dataclass
class TokenUsage:
    """Usage statistics for the completion request."""

    prompt: int
    completion: int


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


@dataclass
class MessageAppend:
    """A chunk of a message generated by the model.

    Attributes:
        content (str, required): A chunk of the message content.
        logprobs (list[Distribution], required): Corresponding log probabilities for each token in the message content.
    """

    content: str
    logprobs: list[Distribution]

    @classmethod
    def from_dict(cls, body: dict[str, Any]) -> "MessageAppend":
        return cls(
            content=body["content"],
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

        if self._finish_reason is None:
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


@dataclass
class MessageBegin:
    role: str


ChatEvent = MessageBegin | MessageAppend | FinishReason | TokenUsage


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

    The content of the message can be streamed by calling `message_content()`.
    If `finish_reason()` or `usage()` has been called, the stream is consumed.


    Attributes:
        role (str, required): The role of the message.
    """

    role: str

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
    def next(self) -> ChatEvent | None:
        """Get the next chat event."""
        ...

    def __init__(self) -> None:
        first_event = self.next()
        if not isinstance(first_event, MessageBegin):
            raise ValueError("Invalid event stream")
        self.role = first_event.role

    def finish_reason(self) -> FinishReason:
        """The reason the model finished generating."""

        if self._finish_reason is None:
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
        deque(self.message_content(), maxlen=0)
        if self._finish_reason is None or self._usage is None:
            raise ValueError("Invalid event stream")

    def message(self) -> Generator[ChatEvent, None, None]:
        """Stream the complete message

        Use this with the @chat decorator to forward all details of the message."""
        yield MessageBegin(self.role)
        yield from self.message_content()
        yield self.finish_reason()
        yield self.usage()

    def message_content(self) -> Generator[MessageAppend, None, None]:
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
        params (CompletionParams, required): Parameters for the requested completion.
    """

    model: str
    prompt: str
    params: CompletionParams


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


class Role(str, Enum):
    """A role used for a message in a chat."""

    User = "user"
    Assistant = "assistant"
    System = "system"


@dataclass
class Message:
    """Describes a message in a chat.

    Parameters:
        role (Role, required): The role of the message.
        content (str, required): The content of the message.
    """

    role: Role
    content: str

    @classmethod
    def user(cls, content: str) -> "Message":
        return cls(role=Role.User, content=content)

    @classmethod
    def assistant(cls, content: str) -> "Message":
        return cls(role=Role.Assistant, content=content)

    @classmethod
    def system(cls, content: str) -> "Message":
        return cls(role=Role.System, content=content)

    @classmethod
    def from_dict(cls, body: dict[str, Any]) -> "Message":
        # the shell csi does not serialize the roles in lowercase
        role = Role(body["role"].lower())
        content = body["content"]
        return cls(role=role, content=content)


@dataclass
class ChatRequest:
    """A chat request that can be sent to the model.

    Attributes:
        model (str, required): Name of model to use.
        messages (list[Message], required): The messages to be sent to the model.
        params (ChatParams, required): Parameters for the requested chat.
    """

    model: str
    messages: list[Message]
    params: ChatParams


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
        granularity (Granularity, optional): Controls the length of the ranges which are explained.
    """

    prompt: str
    target: str
    model: str
    granularity: Granularity = Granularity.AUTO
