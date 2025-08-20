"""
As the bindings for streaming are still behind a feature flag, we can not
require the generated bindings for the corresponding structs (`CompletionAppend`
and `MessageAppend`). We therefore can not use these types for annotations.

The `type: ignore[no-untyped-def]` annotations can be removed once we stabilize
the feature and we know that the classes will always be in the bindings.
"""

import json
from types import TracebackType
from typing import Self

from pharia_skill.csi.inference import (
    ChatEvent,
    ChatStreamResponse,
    CompletionAppend,
    CompletionEvent,
    CompletionStreamResponse,
    Function,
    JsonSchema,
    MessageAppend,
    MessageBegin,
    NamedToolChoice,
    ReasoningEffort,
    ResponseFormat,
    ToolCall,
    ToolCallChunk,
    ToolCallEvent,
    ToolChoice,
)

from ..bindings.imports import inference as wit
from ..csi import (
    ChatParams,
    ChatRequest,
    ChatResponse,
    Completion,
    CompletionParams,
    CompletionRequest,
    Distribution,
    FinishReason,
    Logprob,
    Logprobs,
    Message,
    Role,
    TokenUsage,
    TopLogprobs,
)


class WitCompletionStreamResponse(CompletionStreamResponse):
    def __init__(self, stream: "wit.CompletionStream"):
        self._stream = stream

    def __enter__(self) -> Self:
        self._stream.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        return self._stream.__exit__(exc_type, exc_value, traceback)

    def next(self) -> CompletionEvent | None:
        match self._stream.next():
            case wit.CompletionEvent_Append(value):
                return completion_append_from_wit(value)
            case wit.CompletionEvent_End(value):
                return finish_reason_from_wit(value)
            case wit.CompletionEvent_Usage(value):
                return token_usage_from_wit(value)
            case _:
                return None


class WitChatStreamResponse(ChatStreamResponse):
    def __init__(self, stream: "wit.ChatStream"):
        self._stream = stream
        super().__init__()

    def __enter__(self) -> Self:
        self._stream.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        return self._stream.__exit__(exc_type, exc_value, traceback)

    def _next(self) -> ChatEvent | None:
        match self._stream.next():
            case wit.ChatEvent_MessageBegin(value):
                return MessageBegin(value)
            case wit.ChatEvent_MessageAppend(value):
                return message_append_from_wit(value)
            case wit.ChatEvent_MessageEnd(value):
                return finish_reason_from_wit(value)
            case wit.ChatEvent_Usage(value):
                return token_usage_from_wit(value)
            case wit.ChatEvent_ToolCall(value):
                return ToolCallEvent(
                    tool_calls=[tool_call_chunk_from_wit(t) for t in value]
                )
            case _:
                return None


def chat_params_to_wit(chat_params: ChatParams) -> wit.ChatParams:
    return wit.ChatParams(
        max_tokens=chat_params.max_tokens,
        max_completion_tokens=chat_params.max_completion_tokens,
        temperature=chat_params.temperature,
        top_p=chat_params.top_p,
        frequency_penalty=chat_params.frequency_penalty,
        presence_penalty=chat_params.presence_penalty,
        logprobs=logprobs_to_wit(chat_params.logprobs),
        tools=tools_to_wit(chat_params.tools) if chat_params.tools else None,
        tool_choice=tool_choice_to_wit(chat_params.tool_choice)
        if chat_params.tool_choice
        else None,
        parallel_tool_calls=chat_params.parallel_tool_calls,
        response_format=response_format_to_wit(chat_params.response_format)
        if chat_params.response_format
        else None,
        reasoning_effort=reasoning_effort_to_wit(chat_params.reasoning_effort)
        if chat_params.reasoning_effort
        else None,
    )


def response_format_to_wit(response_format: ResponseFormat) -> wit.ResponseFormat:
    match response_format:
        case "text":
            return wit.ResponseFormat_Text()
        case "json_object":
            return wit.ResponseFormat_JsonObject()
        case JsonSchema():
            return wit.ResponseFormat_JsonSchema(
                value=wit.JsonSchema(
                    name=response_format.name,
                    description=response_format.description,
                    schema=json.dumps(response_format.schema).encode("utf-8"),
                    strict=response_format.strict,
                )
            )


def reasoning_effort_to_wit(reasoning_effort: ReasoningEffort) -> wit.ReasoningEffort:
    match reasoning_effort:
        case ReasoningEffort.LOW:
            return wit.ReasoningEffort.LOW
        case ReasoningEffort.MEDIUM:
            return wit.ReasoningEffort.MEDIUM
        case ReasoningEffort.HIGH:
            return wit.ReasoningEffort.HIGH
        case ReasoningEffort.MINIMAL:
            return wit.ReasoningEffort.MINIMAL


def tools_to_wit(tools: list[Function]) -> list[wit.Function]:
    return [
        wit.Function(
            name=tool.name,
            description=tool.description,
            parameters=json.dumps(tool.parameters).encode("utf-8"),
            strict=tool.strict,
        )
        for tool in tools
    ]


def tool_choice_to_wit(tool_choice: ToolChoice) -> wit.ToolChoice:
    match tool_choice:
        case "none":
            return wit.ToolChoice_None_()
        case "auto":
            return wit.ToolChoice_Auto()
        case "required":
            return wit.ToolChoice_Required()
        case NamedToolChoice():
            return wit.ToolChoice_Named(value=tool_choice.name)
        case _:
            raise ValueError(f"Unknown tool choice: {tool_choice}")


def tool_call_to_wit(tool_call: ToolCall) -> wit.ToolCall:
    return wit.ToolCall(
        id=tool_call.id, name=tool_call.name, arguments=json.dumps(tool_call.arguments)
    )


def tool_call_from_wit(tool_call: wit.ToolCall) -> ToolCall:
    return ToolCall(
        id=tool_call.id,
        name=tool_call.name,
        arguments=json.loads(tool_call.arguments),
    )


def message_to_wit(message: Message) -> wit.Message:
    match message.role:
        case Role.Assistant:
            return wit.Message_Assistant(
                value=wit.AssistantMessage(
                    content=message.content,
                    tool_calls=[tool_call_to_wit(t) for t in message.tool_calls]
                    if message.tool_calls is not None
                    else None,
                )
            )
        case Role.Tool:
            assert message.content is not None
            assert message.tool_call_id is not None
            return wit.Message_Tool(
                value=wit.ToolMessage(
                    content=message.content, tool_call_id=message.tool_call_id
                )
            )
        case _:
            assert message.content is not None
            return wit.Message_Other(
                value=wit.OtherMessage(role=message.role.value, content=message.content)
            )


def chat_request_to_wit(chat_request: ChatRequest) -> wit.ChatRequest:
    return wit.ChatRequest(
        model=chat_request.model,
        messages=[message_to_wit(msg) for msg in chat_request.messages],
        params=chat_params_to_wit(chat_request.params),
    )


def logprob_from_wit(logprob: wit.Logprob) -> Logprob:
    return Logprob(token=logprob.token, logprob=logprob.logprob)


def distribution_from_wit(distribution: wit.Distribution) -> Distribution:
    return Distribution(
        sampled=logprob_from_wit(distribution.sampled),
        top=[logprob_from_wit(logprob) for logprob in distribution.top],
    )


def token_usage_from_wit(usage: wit.TokenUsage) -> TokenUsage:
    return TokenUsage(prompt=usage.prompt, completion=usage.completion)


def tool_call_chunk_from_wit(tool_call_chunk: wit.ToolCallChunk) -> ToolCallChunk:
    return ToolCallChunk(
        index=tool_call_chunk.index,
        id=tool_call_chunk.id,
        name=tool_call_chunk.name,
        arguments=tool_call_chunk.arguments,
    )


def completion_append_from_wit(append: wit.CompletionAppend) -> CompletionAppend:
    return CompletionAppend(
        text=append.text,
        logprobs=[
            distribution_from_wit(distribution) for distribution in append.logprobs
        ],
    )


def message_append_from_wit(append: wit.MessageAppend) -> MessageAppend:
    return MessageAppend(
        content=append.content,
        logprobs=[
            distribution_from_wit(distribution) for distribution in append.logprobs
        ],
    )


def completion_from_wit(completion: wit.Completion) -> Completion:
    return Completion(
        text=completion.text,
        finish_reason=finish_reason_from_wit(completion.finish_reason),
        logprobs=[
            distribution_from_wit(distribution) for distribution in completion.logprobs
        ],
        usage=token_usage_from_wit(completion.usage),
    )


def completion_params_to_wit(
    completion_params: CompletionParams,
) -> wit.CompletionParams:
    return wit.CompletionParams(
        max_tokens=completion_params.max_tokens,
        temperature=completion_params.temperature,
        top_k=completion_params.top_k,
        top_p=completion_params.top_p,
        stop=completion_params.stop,
        return_special_tokens=completion_params.return_special_tokens,
        frequency_penalty=completion_params.frequency_penalty,
        presence_penalty=completion_params.presence_penalty,
        logprobs=logprobs_to_wit(completion_params.logprobs),
        echo=completion_params.echo,
    )


def logprobs_to_wit(logprobs: Logprobs) -> wit.Logprobs:
    match logprobs:
        case "no":
            return wit.Logprobs_No()
        case "sampled":
            return wit.Logprobs_Sampled()
        case TopLogprobs():
            return wit.Logprobs_Top(value=logprobs.top)


def completion_request_to_wit(
    completion_request: CompletionRequest,
) -> wit.CompletionRequest:
    return wit.CompletionRequest(
        model=completion_request.model,
        prompt=completion_request.prompt,
        params=completion_params_to_wit(completion_request.params),
    )


def finish_reason_from_wit(reason: wit.FinishReason) -> FinishReason:
    match reason:
        case wit.FinishReason.STOP:
            return FinishReason.STOP
        case wit.FinishReason.LENGTH:
            return FinishReason.LENGTH
        case wit.FinishReason.CONTENT_FILTER:
            return FinishReason.CONTENT_FILTER
        case wit.FinishReason.TOOL_CALLS:
            return FinishReason.TOOL_CALLS


def message_from_wit(msg: wit.AssistantMessage) -> Message:
    return Message(
        role=Role.Assistant,
        content=msg.content,
        tool_calls=[tool_call_from_wit(t) for t in msg.tool_calls]
        if msg.tool_calls is not None
        else None,
    )


def chat_response_from_wit(response: wit.ChatResponse) -> ChatResponse:
    return ChatResponse(
        message=message_from_wit(response.message),
        finish_reason=finish_reason_from_wit(response.finish_reason),
        logprobs=[
            distribution_from_wit(distribution) for distribution in response.logprobs
        ],
        usage=token_usage_from_wit(response.usage),
    )
