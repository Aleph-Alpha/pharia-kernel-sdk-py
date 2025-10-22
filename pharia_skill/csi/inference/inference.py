"""
This module exposes the interfaces for skills to interact with the PhariaEngine
via the Cognitive System Interface (CSI).
"""

import json
import typing
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

from .types import (
    ChatEvent,
    Distribution,
    FinishReason,
    Message,
    MessageAppend,
    MessageBegin,
    Reasoning,
    Role,
    TokenUsage,
    ToolCall,
    ToolCallEvent,
    _merge_tool_call_chunks,
)

# We don't want to make opentelemetry a dependency of the wasm module
if typing.TYPE_CHECKING:
    from opentelemetry.util.types import AttributeValue


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

    def as_gen_ai_otel_attributes(self) -> dict[str, "AttributeValue"]:
        """The attributes specified by the GenAI Otel Semantic convention.

        See <https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/#genai-attributes>
        for more details.
        """
        attributes: dict[str, "AttributeValue"] = {}

        # According to the OTel specification, the behavior of `None` value attributes
        # is undefined, and hence strongly discouraged.
        if self.max_tokens is not None:
            attributes["gen_ai.request.max_tokens"] = self.max_tokens
        if self.temperature is not None:
            attributes["gen_ai.request.temperature"] = self.temperature
        if self.top_p is not None:
            attributes["gen_ai.request.top_p"] = self.top_p
        if self.frequency_penalty is not None:
            attributes["gen_ai.request.frequency_penalty"] = self.frequency_penalty
        if self.presence_penalty is not None:
            attributes["gen_ai.request.presence_penalty"] = self.presence_penalty
        if self.stop:
            attributes["gen_ai.request.stop_sequences"] = self.stop
        return attributes


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

    _tool_call_chunks: list[ToolCallEvent] | None = None
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

    def __init__(self) -> None:
        self.buffer = []
        first_event = self._next()
        if not isinstance(first_event, MessageBegin):
            raise ValueError(f"Invalid first stream event: {first_event}")
        self.role = first_event.role

    def tool_calls(self) -> list[ToolCall] | None:
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
        if self._tool_call_chunks is None:
            while (event := self._peek()) is not None:
                if isinstance(event, ToolCallEvent):
                    if self._tool_call_chunks is None:
                        self._tool_call_chunks = [event]
                    else:
                        self._tool_call_chunks.append(event)
                else:
                    # once we get a non-tool call event, we can stop accumulating
                    break

        if self._tool_call_chunks is None:
            return None

        tool_calls = _merge_tool_call_chunks(self._tool_call_chunks)

        # If we have found the tool calls, we may exit, allowing the span to be closed.
        self.__exit__(None, None, None)
        return tool_calls

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

    def stream(self) -> Generator[MessageAppend | Reasoning, None, None]:
        """Stream the content of the message.

        This does not include the role, any tool calls, or the finish reason and usage.
        If you are using the tool calling abilties, you should check via `tool_calls()`
        to see if the model is calling a tool.
        """
        if self._usage:
            raise RuntimeError("The stream has already been consumed")
        while (event := self.next()) is not None:
            match event:
                case MessageBegin():
                    raise ValueError("Invalid event stream")
                case Reasoning() | MessageAppend():
                    yield event
                case FinishReason():
                    self._finish_reason = event
                case TokenUsage():
                    self._usage = event

    def consume_message(self) -> Message:
        """A helper method that extracts the contained message from a chat stream.

        This method consumes the stream and only returns the entire messages as long as
        the stream has not been consumed. It can be useful for testing purposes, where
        you are interested in the content of the entire message and not in the
        individual events. In case the stream has already been consumed, an empty
        message is returned.

        Example::

            def test_my_prompt():
                user = Message.user("What is the meaning of life?")
                with csi.chat_stream("llama-3.1-8b-instruct", [user]) as response:
                    message = response.consume_message()

                assert message.content == "42"

        Returns:
            The message of the chat request.
        """
        reasoning_content = ""
        content = ""
        for event in self.stream():
            match event:
                case Reasoning():
                    reasoning_content += event.content
                case MessageAppend():
                    content += event.content
        return Message(
            role=Role(self.role), content=content, reasoning_content=reasoning_content
        )


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

    def as_gen_ai_otel_attributes(self) -> dict[str, "AttributeValue"]:
        """The attributes specified by the GenAI Otel Semantic convention.

        See <https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/#genai-attributes>
        for more details.
        """
        return {
            "gen_ai.content.completion": self.text,
            **self.finish_reason.as_gen_ai_otel_attributes(),
            **self.usage.as_gen_ai_otel_attributes(),
        }


class ReasoningEffort(str, Enum):
    """Constrains effort on reasoning for reasoning models.

    Currently supported values are `minimal`, `low`, `medium`, and `high`.
    Reducing reasoning effort can result in faster responses and fewer tokens used on
    reasoning in a response. Only available for reasoning models (o-series for OpenAI).
    """

    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


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

    def as_gen_ai_otel_attributes(self) -> dict[str, "AttributeValue"]:
        """The attributes specified by the GenAI Otel Semantic convention.

        See <https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/#genai-attributes>
        for more details.
        """
        return {
            "gen_ai.operation.name": "text_completion",
            "gen_ai.request.model": self.model,
            "gen_ai.content.prompt": self.prompt,
            **self.params.as_gen_ai_otel_attributes(),
        }


@dataclass
class Tool:
    """A tool that the model can call."""

    name: str
    """The name of the function to be called. Must be a-z, A-Z, 0-9, or contain underscores and dashes, with a maximum length of 64."""

    description: str | None = None
    """A description of what the function does, used by the model to choose when and how to call the function."""

    parameters: dict[str, Any] | None = None
    """The parameters the functions accepts, described as a JSON Schema object.
    See the [guide](https://platform.openai.com/docs/guides/function-calling?api-mode=responses) for examples,
    and the [JSON Schema reference](https://json-schema.org/understanding-json-schema/reference) for documentation about the format.
    Omitting parameters defines a function with an empty parameter list."""

    strict: bool | None = None
    """Whether to enable strict schema adherence when generating the function call."""


@dataclass
class NamedToolChoice:
    """A tool choice that is a named function."""

    name: str


ToolChoice = Literal["none", "auto", "required"] | NamedToolChoice
"""Controls which (if any) tool is called by the model.

`none` means the model will not call any tool and instead generates a message.
`auto` means the model can pick between generating a message or calling one or more tools.
`required` means the model must call one or more tools.
Specifying a particular tool via `NamedToolChoice` forces the model to call that tool.
`none` is the default when no tools are present. `auto` is the default if tools are present.
"""


@dataclass
class JsonSchema:
    """A JSON Schema object."""

    name: str
    """The name of the response format. Must be a-z, A-Z, 0-9, or contain underscores and dashes, with a maximum length of 64."""
    description: str | None = None
    """A description of what the response format is for, used by the model to determine how to respond in the format."""

    schema: dict[str, Any] | None = None
    """The schema for the response format, described as a JSON Schema object."""

    strict: bool | None = None
    """Whether to enable strict schema adherence when generating the output. If set to true, the model will always follow the exact schema defined in the `schema` field. Only a subset of JSON Schema is supported when `strict` is `true`. To learn more, read the [Structured Outputs guide](https://platform.openai.com/docs/guides/structured-outputs)."""


ResponseFormat = Literal["text", "json_object"] | JsonSchema
"""An object specifying the format that the model must output.

Setting to `JsonSchema` enables Structured Outputs which ensures the model
will match your supplied JSON schema. Learn more in the Structured Outputs guide.

Setting to `"json_object"` enables the older JSON mode, which ensures the message the model generates
is valid JSON. Using json_schema is preferred for models that support it."""


@dataclass
class ChatParams:
    """Chat request parameters.

    Attributes:
        max-tokens (int, optional, default None): The maximum number of tokens that can be generated in the chat completion. This value can be used to control costs for text generated via API. This value is now deprecated by OpenAI in favor of max_completion_tokens, and is not compatible with OpenAI o-series models. Whether to set `max-tokens` or `max-completion-tokens` is an inference provider specific decision. While some inference providers like GitHub models and the Aleph Alpha inference expect the user to set `max-tokens`, OpenAI deprecated it in favor of `max-completion-tokens`. For OpenAI reasoning models, settings `max-tokens` raises an error.
        max-completion-tokens (int, optional, default None): An upper bound for the number of tokens that can be generated for a completion, including visible output tokens and reasoning tokens. Only supported by distinct inference providers (e.g. OpenAI). Note that either `max-tokens` or `max-completion-tokens` can be set, but not both.
        temperature (float, optional, default None): The randomness with which the next token is selected.
        top-p (float, optional, default None): The probability total of next tokens the model will choose from.
        frequency-penalty (float, optional, default None): The presence penalty reduces the probability of generating tokens that are already present in the generated text respectively prompt. Presence penalty is independent of the number of occurrences. Increase the value to reduce the probability of repeating text.
        presence-penalty (float, optional, default None): The presence penalty reduces the probability of generating tokens that are already present in the generated text respectively prompt. Presence penalty is independent of the number of occurrences. Increase the value to reduce the probability of repeating text.
        logprobs (Logprobs, optional, default NoLogprobs()): Use this to control the logarithmic probabilities you want to have returned. This is useful to figure out how likely it had been that this specific token had been sampled.
        tools (list[Function], optional, default None): A list of tools the model may call. Use this to provide a list of functions the model may generate JSON inputs for. A max of 128 functions are supported.
        parallel-tool-calls (bool, optional, default None): Whether to allow the model to call multiple tools in parallel.
        reasoning-effort (ReasoningEffort, optional, default None): Constrains effort on reasoning for reasoning models.
    """

    max_tokens: int | None = None
    max_completion_tokens: int | None = None
    temperature: float | None = None
    top_p: float | None = None
    frequency_penalty: float | None = None
    presence_penalty: float | None = None
    logprobs: Logprobs = "no"
    tools: list[Tool] | None = None
    tool_choice: ToolChoice | None = None
    parallel_tool_calls: bool | None = None
    response_format: ResponseFormat | None = None
    reasoning_effort: ReasoningEffort | None = None

    def as_gen_ai_otel_attributes(self) -> dict[str, "AttributeValue"]:
        attributes: dict[str, "AttributeValue"] = {}

        # According to the OTel specification, the behavior of `None` value attributes
        # is undefined, and hence strongly discouraged.
        if self.max_tokens is not None:
            attributes["gen_ai.request.max_tokens"] = self.max_tokens
        if self.temperature is not None:
            attributes["gen_ai.request.temperature"] = self.temperature
        if self.top_p is not None:
            attributes["gen_ai.request.top_p"] = self.top_p
        if self.frequency_penalty is not None:
            attributes["gen_ai.request.frequency_penalty"] = self.frequency_penalty
        if self.presence_penalty is not None:
            attributes["gen_ai.request.presence_penalty"] = self.presence_penalty
        return attributes


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

    def as_gen_ai_otel_attributes(self) -> dict[str, "AttributeValue"]:
        """The attributes specified by the GenAI Otel Semantic convention.

        See <https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/#genai-attributes>
        for more details.

        Note that the list of attributes specified here is currently not complete, as we
        are still in exploring the conventions.
        """
        return {
            "gen_ai.operation.name": "chat",
            "gen_ai.request.model": self.model,
            "gen_ai.input.messages": json.dumps(
                [m.as_gen_ai_otel_attributes() for m in self.messages]
            ),
            **self.params.as_gen_ai_otel_attributes(),
        }


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

    def as_gen_ai_otel_attributes(self) -> dict[str, "AttributeValue"]:
        """The attributes specified by the GenAI Otel Semantic convention.

        See <https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/#genai-attributes>
        for more details.
        """
        messages = json.dumps([self.message.as_gen_ai_otel_attributes()])
        return {
            "gen_ai.output.messages": messages,
            **self.finish_reason.as_gen_ai_otel_attributes(),
            **self.usage.as_gen_ai_otel_attributes(),
        }
