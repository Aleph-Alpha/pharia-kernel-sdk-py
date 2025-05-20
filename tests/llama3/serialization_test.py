"""
Test that a `ChatRequest` can easily be serialized and deserialized.
If tool calls are done outside the Kernel, the SDK may be used to forward
tool calling ability to the outside world and add a small abstraction on
top of the completion endpoint.
"""

from pydantic import BaseModel, RootModel

from pharia_skill import FinishReason
from pharia_skill.llama3 import (
    AssistantMessage,
    ChatRequest,
    ChatResponse,
    Role,
    Tool,
    ToolCall,
    ToolMessage,
)


class GetGithubReadme(Tool):
    pass


class ChatApi(RootModel[ChatRequest]):
    """Expose a chat api with function calling by forwarding a `ChatRequest`."""

    root: ChatRequest


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
