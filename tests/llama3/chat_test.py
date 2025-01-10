import pytest
from pydantic import BaseModel

from pharia_skill import ChatParams, llama3
from pharia_skill.llama3 import (
    BuiltInTool,
    ChatRequest,
    ChatResponse,
    Message,
    Role,
    ToolCall,
    ToolDefinition,
    ToolResponse,
)
from pharia_skill.testing import DevCsi


@pytest.fixture(scope="module")
def csi() -> DevCsi:
    return DevCsi()


llama_70b = "llama-3.3-70b-instruct"
llama_8b = "llama-3.1-8b-instruct"


class ShipmentParams(BaseModel):
    order_id: str


tool = ToolDefinition(
    name="get_shipment_date",
    description="Get the shipment date for a specific order",
    parameters=ShipmentParams,
)


def test_trigger_tool_call(csi: DevCsi):
    # Given a chat request with a tool definition and a message
    # that requires the tool
    message = Message.user("When will the order `42` ship?")
    request = ChatRequest(messages=[message], tools=[tool])

    # When doing a chat request
    response = llama3.chat(csi, llama_70b, request, ChatParams())

    # Then the response should have a tool call
    assert response.message.role == Role.Assistant
    assert response.message.content is None
    assert response.message.tool_call is not None
    assert response.message.tool_call.tool_name == "get_shipment_date"
    assert response.message.tool_call.arguments == {"order_id": "42"}


def test_provide_tool_result(csi: DevCsi):
    # Given an assistant that has requested a tool call
    user = Message.user("When will the order `42` ship?")
    tool_call = ToolCall(tool_name=tool.name, arguments={"order_id": "42"})
    assistant = Message(role=Role.Assistant, content=None, tool_call=tool_call)

    # When providing a tool response
    tool_response = ToolResponse(
        tool_name=tool.name, status="success", content="1970-01-01"
    )
    ipython = Message.from_tool_response(tool_response)
    request = ChatRequest(messages=[user, assistant, ipython], tools=[tool])

    # Then the response should answer the original question
    response = llama3.chat(csi, llama_70b, request, ChatParams())

    assert response.message.role == Role.Assistant
    assert response.message.tool_call is None
    assert response.message.content is not None
    assert "will ship" in response.message.content
    assert "1970" in response.message.content


def test_chat_response_from_reply():
    reply = "Hello tim!<|eot_id|>"
    chat_response = ChatResponse.from_text(reply)

    assert chat_response.message.content == "Hello tim!"


def test_chat_response_from_reply_with_tool_call():
    reply = "<|python_tag|>def is_prime(n):\n   return True<|eom_id|>"
    chat_response = ChatResponse.from_text(reply)

    assert chat_response.message.content is None
    tool_call = chat_response.message.tool_call
    assert tool_call is not None
    assert tool_call.tool_name == BuiltInTool.CodeInterpreter
    assert tool_call.arguments == {"code": "def is_prime(n):\n   return True"}


def test_tool_call_from_chat_response_without_python_tag():
    """Llama3.3 does not prefix json tool calls with the python tag."""
    text = """{"type": "function", "name": "get_github_readme", "parameters": {"repository": "pharia-kernel"}}"""
    response = ChatResponse.from_text(text)
    assert response.message.content is None
    assert response.message.tool_call is not None
    assert response.message.tool_call.tool_name == "get_github_readme"


def test_tool_call_from_chat_response_with_python_tag():
    text = """\n\n<|python_tag|>{"type": "function", "name": "get_github_readme", "parameters": {"repository": "pharia-kernel"}}"""
    response = ChatResponse.from_text(text)
    assert response.message.content is None
    assert response.message.tool_call is not None
    assert response.message.tool_call.tool_name == "get_github_readme"
