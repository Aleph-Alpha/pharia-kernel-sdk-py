from pharia_skill import (
    ChatParams,
    ChatRequest,
    ChatResponse,
    Completion,
    CompletionParams,
    CompletionRequest,
    Distribution,
    ExplanationRequest,
    FinishReason,
    Granularity,
    Logprob,
    Message,
    Role,
    TextScore,
    TokenUsage,
    TopLogprobs,
)
from pharia_skill.testing.dev.inference import (
    ChatDeserializer,
    ChatRequestSerializer,
    CompletionDeserializer,
    CompletionRequestSerializer,
    ExplanationDeserializer,
    ExplanationRequestSerializer,
)

from .conftest import dumps


def test_serialize_completion_request():
    # Given a list of completion requests
    request = CompletionRequestSerializer(
        requests=[
            CompletionRequest(
                "llama-3.1-8b-instruct",
                "Say hello to Bob",
                CompletionParams(max_tokens=64),
            )
        ]
    )

    # When serializing it
    serialized = request.model_dump_json()

    # Then it nests the structure
    assert serialized == dumps(
        {
            "requests": [
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
                    },
                }
            ]
        }
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
                        "sampled": {"token": [72, 101, 108, 108, 111], "logprob": 0.0},
                        "top": [],
                    }
                ],
                "usage": {"prompt": 0, "completion": 0},
            }
        ]
    )

    # When deserializing it
    deserialized = CompletionDeserializer.model_validate_json(serialized)
    completion = deserialized.root[0]

    # Then the completion is loaded recursively
    assert completion == Completion(
        text="Hello",
        finish_reason=FinishReason.STOP,
        logprobs=[Distribution(sampled=Logprob(token=b"Hello", logprob=0.0), top=[])],
        usage=TokenUsage(prompt=0, completion=0),
    )


def test_serialize_chat_request():
    # Given a list of chat requests
    request = ChatRequestSerializer(
        requests=[
            ChatRequest(
                "llama-3.1-8b-instruct",
                [Message.user("Hello")],
                ChatParams(max_tokens=64, logprobs=TopLogprobs(top=10)),
            )
        ]
    )

    # When serializing it
    serialized = request.model_dump_json()

    # Then it nests the structure
    assert serialized == dumps(
        {
            "requests": [
                {
                    "model": "llama-3.1-8b-instruct",
                    "messages": [{"role": "user", "content": "Hello"}],
                    "params": {
                        "max_tokens": 64,
                        "temperature": None,
                        "top_p": None,
                        "frequency_penalty": None,
                        "presence_penalty": None,
                        "logprobs": {"top": 10},
                    },
                }
            ]
        }
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
                            {"logprob": -0.06857474, "token": [72, 101, 108, 108, 111]}
                        ],
                    }
                ],
                "message": {"content": "Hello", "role": "assistant"},
                "usage": {"completion": 1, "prompt": 11},
            }
        ]
    )

    # When deserializing it
    deserialized = ChatDeserializer.model_validate_json(serialized)
    chat = deserialized.root[0]

    # Then the chat is loaded recursively
    assert chat == ChatResponse(
        finish_reason=FinishReason.LENGTH,
        message=Message(content="Hello", role=Role.Assistant),
        usage=TokenUsage(completion=1, prompt=11),
        logprobs=[
            Distribution(
                sampled=Logprob(token=b"Hello", logprob=-0.06857474),
                top=[Logprob(token=b"Hello", logprob=-0.06857474)],
            )
        ],
    )


def test_serialize_explanation_request():
    # Given a list of Explanation requests
    request = ExplanationRequestSerializer(
        requests=[
            ExplanationRequest(
                prompt="my prompt",
                target="my target",
                model="my-model",
                granularity=Granularity.AUTO,
            )
        ]
    )

    # When serializing it
    serialized = request.model_dump_json()

    # Then it matches
    assert serialized == dumps(
        {
            "requests": [
                {
                    "prompt": "my prompt",
                    "target": "my target",
                    "model": "my-model",
                    "granularity": "auto",
                }
            ]
        }
    )


def test_deserialize_explanation():
    # Given a serialized explanation response
    serialized = dumps([[{"start": 0, "length": 5, "score": 0.5}]])

    # When deserializing it
    deserialized = ExplanationDeserializer.model_validate_json(serialized)
    explanation = deserialized.root

    # Then the explanation is loaded
    assert explanation == [[TextScore(start=0, length=5, score=0.5)]]
