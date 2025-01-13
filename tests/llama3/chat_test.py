import pytest

from pharia_skill import llama3
from pharia_skill.csi import Completion, CompletionParams, Csi, FinishReason
from pharia_skill.llama3 import (
    AssistantMessage,
    ChatRequest,
    Message,
    Role,
    Tool,
    ToolCall,
    ToolResponse,
)
from pharia_skill.testing import DevCsi


@pytest.fixture(scope="module")
def csi() -> DevCsi:
    return DevCsi()


llama = "llama-3.1-8b-instruct"


class GetShipmentDate(Tool):
    """Get the shipment date for a specific order"""

    order_id: str


def test_trigger_tool_call(csi: DevCsi):
    # Given a chat request with a tool definition and a message that requires the tool
    message = Message.user("When will the order `42` ship?")
    request = ChatRequest(llama, [message], [GetShipmentDate])

    # When doing a chat request
    response = llama3.chat(csi, request)

    # Then the response should have a tool call
    assert response.message.role == Role.Assistant
    assert response.message.content is None
    assert response.message.tool_call is not None
    assert response.message.tool_call.name == GetShipmentDate.name()
    assert response.message.tool_call.arguments == {"order_id": "42"}

    # And the original request should be extended
    assert request.messages[-1].role == Role.Assistant


def test_provide_tool_result(csi: DevCsi):
    # Given an assistant that has requested a tool call
    user = Message.user("When will the order `42` ship?")
    tool_call = ToolCall(GetShipmentDate.name(), arguments={"order_id": "42"})
    assistant = AssistantMessage(tool_call=tool_call)

    # When providing a tool response back to the model
    tool = ToolResponse(content="1970-01-01")
    request = ChatRequest(llama, [user, assistant, tool], [GetShipmentDate])
    response = llama3.chat(csi, request)

    # Then the response should answer the original question
    assert response.message.role == Role.Assistant
    assert response.message.tool_call is None
    assert response.message.content is not None
    assert "will ship" in response.message.content
    assert "1970" in response.message.content


class MockCsi(Csi):
    """Csi that can be loaded up with expectations"""

    def __init__(self, completion: Completion):
        self.completion = completion
        self.prompts: list[str] = []

    def complete(self, model: str, prompt: str, params: CompletionParams) -> Completion:
        self.prompts.append(prompt)
        return self.completion


def test_tool_response_can_be_added_to_prompt():
    # Given a chat request with a tool definition and a message that requires the tool
    message = Message.user("When will the order `42` ship?")
    request = ChatRequest(llama, [message], [GetShipmentDate])

    # And given a csi that always responds with a function call
    completion = Completion(
        text='{"type": "function", "name": "get_shipment_date", "parameters": {"order_id": 42}}',
        finish_reason=FinishReason.STOP,
    )
    csi = MockCsi(completion)  #  type: ignore

    # When doing a chat request
    response = llama3.chat(csi, request)
    assert response.message.tool_call is not None

    # And providing the tool response
    tool = ToolResponse(content='{"result": "1970-01-01"}')
    request.extend(tool)

    # And doing another chat request against a spy csi
    response = llama3.chat(csi, request)

    # Then the whole context is included in the second prompt
    expected = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>

Environment: ipython<|eot_id|><|start_header_id|>user<|end_header_id|>

Answer the user\'s question by making use of the following functions if needed.

{
    "type": "function",
    "function": {
        "name": "get_shipment_date",
        "description": "Get the shipment date for a specific order",
        "parameters": {
            "properties": {
                "order_id": {
                    "type": "string"
                }
            },
            "required": [
                "order_id"
            ],
            "type": "object"
        }
    }
}

Return function calls in JSON format.

Question: When will the order `42` ship?<|eot_id|><|start_header_id|>assistant<|end_header_id|>

{"type": "function", "name": "get_shipment_date", "parameters": {"order_id": 42}}<|eom_id|><|start_header_id|>ipython<|end_header_id|>

completed[stdout]{"result": "1970-01-01"}[/stdout]<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
    assert csi.prompts[-1] == expected
