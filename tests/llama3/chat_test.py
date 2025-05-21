import datetime as dt

import pytest

from pharia_skill.csi import (
    Completion,
    CompletionParams,
    Csi,
    FinishReason,
    TokenUsage,
)
from pharia_skill.llama3 import (
    ChatRequest,
    Role,
    ToolCall,
    ToolMessage,
    UserMessage,
)
from pharia_skill.llama3.message import AssistantMessage
from pharia_skill.testing import DevCsi


@pytest.fixture(scope="module")
def csi() -> DevCsi:
    return DevCsi()


llama = "llama-3.3-70b-instruct"


class MockCsi(Csi):
    """Csi that can be loaded up with expectations"""

    def __init__(self, completion: Completion):
        self.completion = completion
        self.prompts: list[str] = []

    def complete(self, model: str, prompt: str, params: CompletionParams) -> Completion:
        self.prompts.append(prompt)
        return self.completion


def test_can_not_chat_twice_without_appending_message():
    # Given a chat request after a chat request
    message = UserMessage("What is the meaning of life?")
    request = ChatRequest(llama, [message])
    completion = Completion(
        text="42",
        finish_reason=FinishReason.STOP,
        logprobs=[],
        usage=TokenUsage(prompt=len(message.content), completion=len(message.content)),
    )
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
    completion = Completion(
        text="42",
        finish_reason=FinishReason.STOP,
        logprobs=[],
        usage=TokenUsage(prompt=len(message.content), completion=len(message.content)),
    )
    csi = MockCsi(completion)  # type: ignore

    request.chat(csi)

    # When extending the request with a user response
    request.extend(UserMessage("Are you sure?"))

    # Then another chat request can be done
    request.chat(csi)


@pytest.mark.kernel
def test_trigger_tool_call(csi: DevCsi):
    # Given a chat request with a tool definition and a message that requires the tool
    message = UserMessage("What is the population of Paris?")
    request = ChatRequest(llama, [message], tools=["population_tool"])

    # When doing a chat request
    response = request.chat(csi)

    # Then the response should have a tool call
    assert response.message.role == Role.Assistant
    assert response.message.content is None
    assert response.message.tool_calls
    assert response.message.tool_calls[0].name == "population_tool"
    assert response.message.tool_calls[0].parameters == {"city": "Paris"}

    # And the original request should be extended
    assert request.messages[-1].role == Role.Assistant


@pytest.mark.kernel
def test_provide_tool_result(csi: DevCsi):
    # Given an assistant that has requested a tool call
    user = UserMessage("How many people live in Paris?")
    tool_call = ToolCall("population_tool", parameters={"city": "Paris"})
    assistant = AssistantMessage(tool_calls=[tool_call])

    # When providing a tool response back to the model
    tool = ToolMessage(content="71 million people")
    request = ChatRequest(llama, [user, assistant, tool], tools=["population_tool"])
    response = request.chat(csi)

    # Then the response should answer the original question
    assert response.message.role == Role.Assistant
    assert response.message.tool_calls is None
    assert response.message.content is not None
    assert "71 million" in response.message.content


def test_tool_response_can_be_added_to_prompt():
    # Given a chat request with a tool definition and a message that requires the tool
    message = UserMessage("How many people live in Paris?")
    request = ChatRequest(llama, [message], tools=["population_tool"])

    # And given a csi that always responds with a function call
    completion = Completion(
        text='{"type": "function", "name": "population_tool", "parameters": {"city": "Paris"}}',
        finish_reason=FinishReason.STOP,
        logprobs=[],
        usage=TokenUsage(prompt=len(message.content), completion=len(message.content)),
    )
    csi = MockCsi(completion)  #  type: ignore

    # When doing a chat request
    response = request.chat(csi)
    assert response.message.tool_calls
    assert response.message.tool_calls[0].parameters == {"city": "Paris"}

    # And providing the tool response
    tool = ToolMessage(content='{"result": "71 million"}')
    request.extend(tool)

    # And doing another chat request against a spy csi
    response = request.chat(csi)

    # Then the whole context is included in the second prompt
    expected = (
        """<|begin_of_text|><|start_header_id|>system<|end_header_id|>

Environment: ipython
Cutting Knowledge Date: December 2023"""
        f"\nToday Date: {dt.datetime.now().strftime('%d %B %Y')}"
        """\n\nAnswer the user's question by making use of the following functions if needed.
Only use functions if they are relevant to the user's question.
Here is a list of functions in JSON format:
{
    "type": "function",
    "function": {
        "name": "population_tool",
        "description": "Return the number of people living in a city",
        "parameters": {
            "properties": {
                "city": {
                    "type": "string"
                }
            },
            "required": [
                "city"
            ],
            "type": "object"
        }
    }
}

Return function calls in JSON format.

You are a helpful assistant.<|eot_id|><|start_header_id|>user<|end_header_id|>

How many people live in Paris?<|eot_id|><|start_header_id|>assistant<|end_header_id|>

<|python_tag|>{"name": "population_tool", "parameters": {"city": "Paris"}}<|eom_id|><|start_header_id|>ipython<|end_header_id|>

completed[stdout]{"result": "71 million"}[/stdout]<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
    )
    assert csi.prompts[-1] == expected
