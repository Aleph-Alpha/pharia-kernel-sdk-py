"""
Test that a `ChatRequest` can easily be serialized and deserialized.
If tool calls are done outside the Kernel, the SDK may be used to forward
tool calling ability to the outside world and add a small abstraction on
top of the completion endpoint.
"""

import pytest
from pydantic import BaseModel, RootModel

from pharia_skill import FinishReason
from pharia_skill.llama3 import (
    AssistantMessage,
    ChatRequest,
    ChatResponse,
    CodeInterpreter,
    JsonSchema,
    Role,
    Tool,
    ToolCall,
    ToolMessage,
    UserMessage,
)


class GetGithubReadme(Tool):
    pass


class ChatApi(RootModel[ChatRequest]):
    """Expose a chat api with function calling by forwarding a `ChatRequest`."""

    root: ChatRequest


def test_chat_request_field_serializer_built_in_tool():
    request = ChatRequest("llama-3.1-8b-instruct", [UserMessage("Hi")])
    tools = [CodeInterpreter]

    serialized = request.as_dict(tools)

    assert serialized == [{"type": "code_interpreter"}]


def test_chat_request_field_serializer_custom_typed_tool():
    request = ChatRequest("llama-3.1-8b-instruct", [UserMessage("Hi")])
    tools = [GetGithubReadme]

    serialized = request.as_dict(tools)
    assert serialized == [
        {
            "type": "function",
            "function": {
                "name": "get_github_readme",
                "description": None,
                "parameters": {
                    "properties": {},
                    "type": "object",
                },
            },
        }
    ]


def test_chat_request_field_serializer_custom_tool():
    request = ChatRequest("llama-3.1-8b-instruct", [UserMessage("Hi")])
    data = {
        "type": "function",
        "function": {
            "name": "custom-tool-definition",
            "description": "Custom Tool",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    }
    tool = JsonSchema(**data)  # type: ignore
    serialized = request.as_dict([tool])
    assert serialized == [data]


def test_chat_request_validate_built_in_tool():
    serialized = [{"type": "code_interpreter"}]
    validated = ChatRequest.validate_tools(serialized)  # type: ignore
    assert validated == [CodeInterpreter]


def test_chat_request_validate_unknown_tool():
    serialized = ["unknown_tool"]
    with pytest.raises(AssertionError):
        ChatRequest.validate_tools(serialized)  # type: ignore


def test_chat_request_validate_custom_tool():
    schema = {
        "type": "function",
        "function": {
            "name": "custom-tool-definition",
            "description": "Custom Tool",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    }
    serialized = [schema]
    validated = ChatRequest.validate_tools(serialized)  # type: ignore
    assert validated == [JsonSchema(**schema)]  # type: ignore


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
    assert isinstance(chat.root.tools[0], JsonSchema)
    assert chat.root.tools[0].name() == "get_github_readme"
    assert chat.root.messages[0].role == Role.User


def test_built_in_tool_can_be_deserialized():
    data = {
        "model": "llama-3.1-8b-instruct",
        "tools": [{"type": "code_interpreter"}],
        "messages": [
            {
                "role": "user",
                "content": "Hello, World!",
            }
        ],
    }
    chat = ChatApi.model_validate(data)
    assert len(chat.root.tools) == 1
    assert chat.root.tools[0] == CodeInterpreter


def test_tool_result_can_be_deserialized():
    # Given a chat request with a tool call and a tool response
    data = {
        "model": "llama-3.1-8b-instruct",
        "system": "You are a helpful assistant",
        "messages": [
            {
                "role": "user",
                "content": "When will my order (42) arrive?",
            },
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "name": "get_delivery_date",
                        "parameters": {"order_id": "123456"},
                    }
                ],
            },
            {
                "role": "ipython",
                "content": "2025-07-01",
            },
            {
                "role": "assistant",
                "content": "It will be delivered in July 2025.",
            },
            {
                "role": "user",
                "content": "Thank you!",
            },
        ],
    }

    # When deserializing it to the ChatApi model
    chat = ChatApi.model_validate(data)

    # Then we get four messages
    messages = chat.root.messages
    assert len(messages) == 5

    # And the first one is a user message
    assert messages[0].role == Role.User

    # And the second one is an assistant one
    assert isinstance(messages[1], AssistantMessage)
    assert messages[1].tool_calls
    assert messages[1].tool_calls[0].name == "get_delivery_date"

    # And the third one is a tool response
    assert isinstance(messages[2], ToolMessage)
    assert chat.root.messages[2].content == "2025-07-01"

    # And the fourth one is an assistant message
    assert messages[3].role == Role.Assistant
    assert messages[3].content == "It will be delivered in July 2025."

    # And we receive a system prompt
    assert chat.root.system == "You are a helpful assistant"


class ChatOutput(RootModel[ChatResponse]):
    """The caller just receives one message back.

    State needs to be maintained on the caller side.
    """

    root: ChatResponse


def test_chat_response_can_be_serialized():
    # Given a chat response with a function call
    tool_call = ToolCall(name="get_shipment_date", parameters={"order_id": "42"})
    message = AssistantMessage(tool_calls=[tool_call])
    response = ChatResponse(message, FinishReason.STOP)

    # When serializing it via `ChatOutput`
    data = ChatOutput(root=response).model_dump_json(indent=4)
    expected = """{
    "message": {
        "content": null,
        "role": "assistant",
        "tool_calls": [
            {
                "name": "get_shipment_date",
                "parameters": {
                    "order_id": "42"
                }
            }
        ]
    },
    "finish_reason": "stop"
}"""

    assert data == expected


def test_tool_call_can_be_deserialized():
    # given a tool call wrapped in a pydantic model
    class Wrapper(BaseModel):
        tool_call: ToolCall

    # when deserializing the wrapper
    data = {"tool_call": {"name": "get_delivery_date", "parameters": {"order_id": 42}}}
    tool_call = Wrapper.model_validate(data)

    # then the tool call is serialized into a dict
    assert tool_call.tool_call.name == "get_delivery_date"
    assert tool_call.tool_call.parameters == {"order_id": 42}
