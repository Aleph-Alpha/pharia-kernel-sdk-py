"""
Test that a `ChatRequest` can easily be serialized and deserialized.
If tool calls are done outside the Kernel, the SDK may be used to forward
tool calling ability to the outside world and add a small abstraction on
top of the completion endpoint.
"""

from pydantic import RootModel

from pharia_skill import FinishReason
from pharia_skill.llama3 import (
    AssistantMessage,
    ChatRequest,
    ChatResponse,
    Role,
    ToolCall,
    ToolResponse,
)


class ChatApi(RootModel[ChatRequest]):
    """Expose a chat api with function calling by forwarding a `ChatRequest`."""

    root: ChatRequest


def test_chat_request_can_be_deserialized():
    # Given a dictionary representation of a `ChatRequest`
    data = {
        "model": "llama-3.1-8b-instruct",
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "get_github_readme",
                    "description": "Get the readme of a GitHub repository",
                    "parameters": {
                        "type": "object",
                        "required": ["repository"],
                        "properties": {
                            "repository": {
                                "type": "string",
                                "description": "The name of the GitHub repository to get the readme from",
                            },
                            "registry": {"type": "string", "default": "default"},
                        },
                    },
                },
            }
        ],
        "messages": [
            {
                "role": "user",
                "content": "Hello, World!",
            }
        ],
    }

    # When deserializing it to the ChatApi model
    chat = ChatApi.model_validate(data)

    # Then the request is serialized successfully
    assert len(chat.root.messages) == 1
    assert len(chat.root.tools) == 1
    assert isinstance(chat.root.tools[0], dict)
    assert chat.root.tools[0]["function"]["name"] == "get_github_readme"
    assert chat.root.messages[0].role == Role.User


def test_built_in_tool_can_be_deserialized():
    data = {
        "model": "llama-3.1-8b-instruct",
        "tools": ["code_interpreter"],
        "messages": [
            {
                "role": "user",
                "content": "Hello, World!",
            }
        ],
    }
    chat = ChatApi.model_validate(data)
    assert len(chat.root.tools) == 1
    assert chat.root.tools[0] == "code_interpreter"


def test_tool_result_can_be_deserialized():
    # Given a chat request with a tool call and a tool response
    data = {
        "model": "llama-3.1-8b-instruct",
        "messages": [
            {
                "role": "user",
                "content": "When will my order (42) arrive?",
            },
            {
                "role": "assistant",
                "tool_calls": [
                    {
                        "type": "function",
                        "function": {
                            "name": "get_delivery_date",
                            "parameters": '{"order_id":"123456"}',
                        },
                    }
                ],
            },
            {
                "role": "ipython",
                "content": "2025-07-01",
            },
        ],
    }

    # When deserializing it to the ChatApi model
    chat = ChatApi.model_validate(data)

    # Then we get three messages
    messages = chat.root.messages
    assert len(messages) == 3

    # And the third one is a tool response
    assert isinstance(messages[2], ToolResponse)
    assert chat.root.messages[2].content == "2025-07-01"

    # And the second one is an assistant one
    assert isinstance(messages[1], AssistantMessage)

    # And the first one is a user message
    assert messages[0].role == Role.User


class ChatOutput(RootModel[ChatResponse]):
    """The caller just receives one message back.

    State needs to be maintained on the caller side.
    """

    root: ChatResponse


def test_chat_response_can_be_serialized():
    # Given a chat response with a function call
    tool_call = ToolCall(name="get_shipment_date", arguments={"order_id": "42"})
    message = AssistantMessage(tool_call=tool_call)
    response = ChatResponse(message, FinishReason.STOP)

    # When serializing it via `ChatOutput`
    data = ChatOutput(root=response).model_dump_json(indent=4)
    expected = """{
    "message": {
        "content": null,
        "role": "assistant",
        "tool_call": {
            "name": "get_shipment_date",
            "arguments": {
                "order_id": "42"
            }
        }
    },
    "finish_reason": "stop"
}"""

    assert data == expected
