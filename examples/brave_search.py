"""
A skill that can use function calling to search the web.
"""

from pydantic import BaseModel

from pharia_skill import ChatParams, Csi, skill
from pharia_skill.llama3 import ChatRequest, Tool, ToolMessage, UserMessage


class Input(BaseModel):
    question: str


class Output(BaseModel):
    answer: str


class PopulationTool(Tool):
    """Return the number of people living in a city"""

    city: str

    def execute(self) -> str:
        if self.city == "Paris":
            return "90 Million"
        raise ValueError(f"Unknown city: {self.city}")


@skill
def brave_search(csi: Csi, input: Input) -> Output:
    request = ChatRequest(
        model="llama-3.3-70b-instruct",
        messages=[UserMessage(content=input.question)],
        params=ChatParams(),
        tools=[PopulationTool],
    )
    response = request.chat(csi)
    if response.message.tool_calls:
        tool_call = response.message.tool_calls[0].parameters
        assert isinstance(tool_call, PopulationTool)

        result = tool_call.execute()
        request.extend(ToolMessage(content=result))
        response = request.chat(csi)
        assert response.message.content is not None
        return Output(answer=response.message.content)
    else:
        assert response.message.content is not None
        return Output(answer=response.message.content)
