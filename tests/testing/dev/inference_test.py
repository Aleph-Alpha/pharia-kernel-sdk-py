from math import isnan

import pytest

from pharia_skill import (
    ChatParams,
    ChatRequest,
    ChatResponse,
    Completion,
    CompletionParams,
    CompletionRequest,
    Distribution,
    FinishReason,
    Logprob,
    Message,
    Role,
    TokenUsage,
    TopLogprobs,
)
from pharia_skill.csi.inference import (
    CompletionAppend,
    MessageAppend,
    MessageBegin,
    ToolCall,
)
from pharia_skill.testing.dev.client import Event
from pharia_skill.testing.dev.inference import (
    ChatListDeserializer,
    ChatRequestListSerializer,
    CompletionListDeserializer,
    CompletionRequestListSerializer,
    chat_event_from_sse,
    completion_event_from_sse,
)

from .conftest import dumps


def test_serialize_completion_request():
    # Given a list of completion requests
    request = CompletionRequestListSerializer(
        [
            CompletionRequest(
                "llama-3.1-8b-instruct",
                "Say hello to Bob",
                CompletionParams(max_tokens=64, echo=True),
            )
        ]
    )

    # When serializing it
    serialized = request.model_dump_json()

    # Then
    assert serialized == dumps(
        [
            {
                "model": "llama-3.1-8b-instruct",
                "prompt": "Say hello to Bob",
                "params": {
                    "max_tokens": 64,
                    "temperature": None,
                    "top_k": None,
                    "top_p": None,
                    "stop": [],
                    "return_special_tokens": True,
                    "frequency_penalty": None,
                    "presence_penalty": None,
                    "logprobs": "no",
                    "echo": True,
                },
            }
        ]
    )


def test_deserialize_completion():
    # Given a serialized completion response
    serialized = dumps(
        [
            {
                "text": "Hello",
                "finish_reason": "stop",
                "logprobs": [
                    {
                        "sampled": {
                            "token": [72, 101, 108, 108, 111],
                            "logprob": 0.0,
                        },
                        "top": [],
                    }
                ],
                "usage": {"prompt": 0, "completion": 0},
            }
        ]
    )

    # When deserializing it
    deserialized = CompletionListDeserializer.model_validate_json(serialized)
    completion = deserialized.root[0]

    # Then the completion is loaded recursively
    assert completion == Completion(
        text="Hello",
        finish_reason=FinishReason.STOP,
        logprobs=[Distribution(sampled=Logprob(token=b"Hello", logprob=0.0), top=[])],
        usage=TokenUsage(prompt=0, completion=0),
    )


def test_deserialize_completion_with_logprob_nan():
    # Given a serialized completion response without a logprob
    serialized = dumps(
        [
            {
                "text": "Hello",
                "finish_reason": "stop",
                "logprobs": [
                    {
                        "sampled": {
                            "token": [72, 101, 108, 108, 111],
                            "logprob": None,
                        },
                        "top": [],
                    }
                ],
                "usage": {"prompt": 0, "completion": 0},
            }
        ]
    )

    # When deserializing it
    deserialized = CompletionListDeserializer.model_validate_json(serialized)
    completion = deserialized.root[0]

    # Then the sampled logprob is parsed as NaN
    assert isnan(completion.logprobs[0].sampled.logprob)


def test_tool_call_arguments_get_serialized_as_json():
    # Given a tool call
    tool_call = ToolCall(
        id="tool_call_id", name="tool_name", arguments={"a": 1, "b": 2}
    )
    message = Message.assistant("Hello", tool_calls=[tool_call])
    request = ChatRequest("llama-3.1-8b-instruct", [message])

    # When serializing it
    serialized = ChatRequestListSerializer([request]).model_dump_json()

    # Then the tool call arguments are serialized as JSON
    assert serialized == dumps(
        [
            {
                "model": "llama-3.1-8b-instruct",
                "messages": [
                    {
                        "role": "assistant",
                        "content": "Hello",
                        "reasoning_content": None,
                        "tool_calls": [
                            {
                                "id": "tool_call_id",
                                "name": "tool_name",
                                "arguments": '{"a": 1, "b": 2}',
                            }
                        ],
                        "tool_call_id": None,
                    }
                ],
                "params": {
                    "max_tokens": None,
                    "max_completion_tokens": None,
                    "temperature": None,
                    "top_p": None,
                    "frequency_penalty": None,
                    "presence_penalty": None,
                    "logprobs": "no",
                    "tools": None,
                    "tool_choice": None,
                    "parallel_tool_calls": None,
                    "response_format": None,
                    "reasoning_effort": None,
                },
            }
        ]
    )


def test_serialize_chat_request():
    # Given a list of chat requests
    request = ChatRequestListSerializer(
        [
            ChatRequest(
                "llama-3.1-8b-instruct",
                [Message.user("Hello")],
                ChatParams(max_tokens=64, logprobs=TopLogprobs(top=10)),
            )
        ]
    )

    # When serializing it
    serialized = request.model_dump_json()

    # Then
    assert serialized == dumps(
        [
            {
                "model": "llama-3.1-8b-instruct",
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello",
                        "reasoning_content": None,
                        "tool_calls": None,
                        "tool_call_id": None,
                    }
                ],
                "params": {
                    "max_tokens": 64,
                    "max_completion_tokens": None,
                    "temperature": None,
                    "top_p": None,
                    "frequency_penalty": None,
                    "presence_penalty": None,
                    "logprobs": {"top": 10},
                    "tools": None,
                    "tool_choice": None,
                    "parallel_tool_calls": None,
                    "response_format": None,
                    "reasoning_effort": None,
                },
            }
        ]
    )


def test_deserialize_chat():
    # Given a serialized chat response
    serialized = dumps(
        [
            {
                "finish_reason": "length",
                "logprobs": [
                    {
                        "sampled": {
                            "logprob": -0.06857474,
                            "token": [72, 101, 108, 108, 111],
                        },
                        "top": [
                            {
                                "logprob": -0.06857474,
                                "token": [72, 101, 108, 108, 111],
                            }
                        ],
                    }
                ],
                "message": {
                    "content": "Hello",
                    "reasoning_content": "I'm thinking...",
                    "role": "assistant",
                },
                "usage": {"completion": 1, "prompt": 11},
            }
        ]
    )

    # When deserializing it
    deserialized = ChatListDeserializer.model_validate_json(serialized)
    chat = deserialized.root[0]

    # Then the chat is loaded recursively
    assert chat == ChatResponse(
        finish_reason=FinishReason.LENGTH,
        message=Message(
            content="Hello", role=Role.Assistant, reasoning_content="I'm thinking..."
        ),
        usage=TokenUsage(completion=1, prompt=11),
        logprobs=[
            Distribution(
                sampled=Logprob(token=b"Hello", logprob=-0.06857474),
                top=[Logprob(token=b"Hello", logprob=-0.06857474)],
            )
        ],
    )


def test_deserialize_completion_append_from_sse():
    # Given a completion event append
    payload = {"text": "Hello", "logprobs": []}
    event = Event(event="append", data=payload)

    # When deserializing it
    deserialized = completion_event_from_sse(event)

    # Then the completion event is loaded
    assert deserialized == CompletionAppend(text="Hello", logprobs=[])


def test_deserialize_completion_end_from_sse():
    # Given a completion event end
    payload = {"finish_reason": "stop"}
    event = Event(event="end", data=payload)

    # When deserializing it
    deserialized = completion_event_from_sse(event)

    # Then the completion event is loaded
    assert deserialized == FinishReason.STOP


def test_deserialize_completion_usage_from_sse():
    # Given a completion event usage
    payload = {"usage": {"prompt": 1, "completion": 1}}
    event = Event(event="usage", data=payload)

    # When deserializing it
    deserialized = completion_event_from_sse(event)

    # Then the completion event is loaded
    assert deserialized == TokenUsage(prompt=1, completion=1)


def test_deserialize_chat_message_begin_from_sse():
    # Given a chat event message begin
    payload = {"role": "user"}
    event = Event(event="message_begin", data=payload)

    # When deserializing it
    deserialized = chat_event_from_sse(event)

    # Then the chat event is loaded
    assert deserialized == MessageBegin(role=Role.User)


def test_deserialize_chat_message_append_from_sse():
    # Given a chat event message append
    payload = {"content": "Hello", "logprobs": []}
    event = Event(event="message_append", data=payload)

    # When deserializing it
    deserialized = chat_event_from_sse(event)

    # Then the chat event is loaded
    assert deserialized == MessageAppend(content="Hello", logprobs=[])


def test_deserialize_chat_message_end_from_sse():
    # Given a chat event message end
    payload = {"finish_reason": "stop"}
    event = Event(event="message_end", data=payload)

    # When deserializing it
    deserialized = chat_event_from_sse(event)

    # Then the chat event is loaded
    assert deserialized == FinishReason.STOP


def test_deserialize_chat_usage_from_sse():
    # Given a chat event usage
    payload = {"usage": {"prompt": 1, "completion": 1}}
    event = Event(event="usage", data=payload)

    # When deserializing it
    deserialized = chat_event_from_sse(event)

    # Then the chat event is loaded
    assert deserialized == TokenUsage(prompt=1, completion=1)


def test_error_event_raises_error_with_good_message():
    # Given an error event
    payload = {
        "message": "Sorry, We could not find the skill you requested in its namespace."
    }
    event = Event(event="error", data=payload)

    # When deserializing it
    with pytest.raises(ValueError) as e:
        chat_event_from_sse(event)

    # Then the error message is as expected
    assert str(e.value).startswith("Unexpected event:")
