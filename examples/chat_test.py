from examples.chat import ChatApi, chat_api
from pharia_skill.llama3 import ChatRequest, Tool, UserMessage
from pharia_skill.testing import DevCsi


class GetShipmentDate(Tool):
    """Get the shipment date for a specific order"""

    order_id: int


def test_chat_api():
    # Given a chat api request with a user message and a tool definition
    csi = DevCsi()
    user = UserMessage("When will my order (42) arrive?")
    request = ChatRequest("llama-3.1-8b-instruct", [user], [GetShipmentDate])
    input = ChatApi(root=request)

    # When the chat api is called
    result = chat_api(csi, input).root

    # Then a function call is returned
    assert result.message.tool_calls
    assert isinstance(result.message.tool_calls[0].parameters, GetShipmentDate)
    assert result.message.tool_calls[0].parameters.order_id == 42
