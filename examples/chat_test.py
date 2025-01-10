from pydantic import BaseModel

from examples.chat import ChatApi, chat_api
from pharia_skill.llama3 import ChatRequest, Message, ToolDefinition
from pharia_skill.testing import DevCsi


class ShippingParams(BaseModel):
    order_id: int


def test_chat_api():
    # Given a chat api request with a user message and a tool definition
    csi = DevCsi()
    user = Message.user("When will my order (42) arrive?")
    tool = ToolDefinition(
        name="get_shipment_date",
        description="Get the shipment date for a specific order",
        parameters=ShippingParams,
    )
    request = ChatRequest("llama-3.1-8b-instruct", [user], [tool])
    input = ChatApi(root=request)

    # When the chat api is called
    result = chat_api(csi, input).root

    # Then a function call is returned
    assert result.message.tool_call is not None
    assert result.message.tool_call.tool_name == "get_shipment_date"
    assert result.message.tool_call.arguments == {"order_id": "42"}


def test_model_dump():
    user = Message.user("When will my order (42) arrive?")
    tool = ToolDefinition(
        name="get_shipment_date",
        description="Get the shipment date for a specific order",
        parameters=ShippingParams,
    )
    request = ChatRequest("llama-3.1-8b-instruct", [user], [tool])
    input = ChatApi(root=request)
    input.model_dump_json()
