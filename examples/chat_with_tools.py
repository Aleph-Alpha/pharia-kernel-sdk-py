"""
A skill that can use function calling to search the web.
"""

from pydantic import BaseModel

from pharia_skill import ChatParams, Csi, skill
from pharia_skill.llama3.message import ToolMessage, UserMessage
from pharia_skill.llama3.request import ChatRequest


class Input(BaseModel):
    question: str


class Output(BaseModel):
    answer: str


@skill
def chat_with_tools(csi: Csi, input: Input) -> Output:
    request = ChatRequest(
        model="llama-3.3-70b-instruct",
        messages=[UserMessage(content=input.question)],
        params=ChatParams(),
        tools=["population_tool"],
    )
    response = request.chat(csi)
    if response.message.tool_calls:
        tool_call = response.message.tool_calls[0]
        result = csi.invoke_tool(tool_call.name, tool_call.parameters)
        request.extend(ToolMessage(content=result))
        response = request.chat(csi)
        assert response.message.content is not None
        return Output(answer=response.message.content)
    raise ValueError(f"No tool call found in response: {response.message}")
