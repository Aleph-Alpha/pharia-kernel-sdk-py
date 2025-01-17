import pytest

from pharia_skill.csi import Completion, CompletionParams, Csi, FinishReason
from pharia_skill.llama3 import (
    ChatRequest,
    Role,
    Tool,
    ToolCall,
    ToolMessage,
    UserMessage,
)
from pharia_skill.llama3.message import AssistantMessage
from pharia_skill.testing import DevCsi


@pytest.fixture(scope="module")
def csi() -> DevCsi:
    return DevCsi()


llama = "llama-3.1-8b-instruct"


class MockCsi(Csi):
    """Csi that can be loaded up with expectations"""

    def __init__(self, completion: Completion):
        self.completion = completion
        self.prompts: list[str] = []

    def complete(self, model: str, prompt: str, params: CompletionParams) -> Completion:
        self.prompts.append(prompt)
        return self.completion


class GetShipmentDate(Tool):
    """Get the shipment date for a specific order"""

    order_id: str


def test_can_not_chat_twice_without_appending_message():
    # Given a chat request after a chat request
    message = UserMessage("What is the meaning of life?")
    request = ChatRequest(llama, [message])
    completion = Completion(text="42", finish_reason=FinishReason.STOP)
    csi = MockCsi(completion)  # type: ignore

    request.chat(csi)

    # When doing another chat request
    with pytest.raises(ValueError):
        # Then an error should be raised
        request.chat(csi)


def test_can_chat_twice_when_providing_user_response():
    # Given a chat request after a chat request
    message = UserMessage("What is the meaning of life?")
    request = ChatRequest(llama, [message])
    completion = Completion(text="42", finish_reason=FinishReason.STOP)
    csi = MockCsi(completion)  # type: ignore

    request.chat(csi)

    # When extending the request with a user response
    request.extend(UserMessage("Are you sure?"))

    # Then another chat request can be done
    request.chat(csi)


@pytest.mark.kernel
def test_trigger_tool_call(csi: DevCsi):
    # Given a chat request with a tool definition and a message that requires the tool
    message = UserMessage("When will the order `42` ship?")
    request = ChatRequest(llama, [message], tools=[GetShipmentDate])

    # When doing a chat request
    response = request.chat(csi)

    # Then the response should have a tool call
    assert response.message.role == Role.Assistant
    assert response.message.content is None
    assert response.message.tool_calls
    assert isinstance(response.message.tool_calls[0].arguments, GetShipmentDate)
    assert response.message.tool_calls[0].arguments.order_id == "42"

    # And the original request should be extended
    assert request.messages[-1].role == Role.Assistant


@pytest.mark.kernel
def test_provide_tool_result(csi: DevCsi):
    # Given an assistant that has requested a tool call
    user = UserMessage("When will the order `42` ship?")
    tool_call = ToolCall(GetShipmentDate.name(), arguments={"order_id": "42"})
    assistant = AssistantMessage(tool_calls=[tool_call])

    # When providing a tool response back to the model
    tool = ToolMessage(content="1970-01-01")
    request = ChatRequest(llama, [user, assistant, tool], [GetShipmentDate])
    response = request.chat(csi)

    # Then the response should answer the original question
    assert response.message.role == Role.Assistant
    assert response.message.tool_calls is None
    assert response.message.content is not None
    assert "will ship" in response.message.content
    assert "1970" in response.message.content


def test_tool_response_is_parsed_into_provided_class():
    # Given a tool specified as pydantic model
    message = UserMessage("When will the order `42` ship?")
    request = ChatRequest(llama, [message], [GetShipmentDate])
    completion = Completion(
        text='{"type": "function", "name": "get_shipment_date", "parameters": {"order_id": "42"}}',
        finish_reason=FinishReason.STOP,
    )
    csi = MockCsi(completion)  #  type: ignore

    # When doing a completion request
    response = request.chat(csi)

    # Then the response is parsed into the provided class
    assert response.message.tool_calls
    assert isinstance(response.message.tool_calls[0].arguments, GetShipmentDate)


def test_tool_response_can_be_added_to_prompt():
    # Given a chat request with a tool definition and a message that requires the tool
    message = UserMessage("When will the order `42` ship?")
    request = ChatRequest(llama, [message], [GetShipmentDate])

    # And given a csi that always responds with a function call
    completion = Completion(
        text='{"type": "function", "name": "get_shipment_date", "parameters": {"order_id": "42"}}',
        finish_reason=FinishReason.STOP,
    )
    csi = MockCsi(completion)  #  type: ignore

    # When doing a chat request
    response = request.chat(csi)
    assert response.message.tool_calls
    assert isinstance(response.message.tool_calls[0].arguments, GetShipmentDate)

    # And providing the tool response
    tool = ToolMessage(content='{"result": "1970-01-01"}')
    request.extend(tool)

    # And doing another chat request against a spy csi
    response = request.chat(csi)

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

{"type": "function", "name": "get_shipment_date", "parameters": {"order_id": "42"}}<|eom_id|><|start_header_id|>ipython<|end_header_id|>

completed[stdout]{"result": "1970-01-01"}[/stdout]<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
    assert csi.prompts[-1] == expected
