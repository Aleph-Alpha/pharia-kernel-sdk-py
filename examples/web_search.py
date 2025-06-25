from pydantic import BaseModel

from pharia_skill import Csi, ToolError, skill
from pharia_skill.llama3 import ChatRequest, Tool, ToolMessage
from pharia_skill.llama3.request import Message


class Input(BaseModel):
    messages: list[Message]


class Output(BaseModel):
    message: list[Message]


class Search(Tool):
    """Search the web for the given query for links to relevant pages."""

    query: str


class Fetch(Tool):
    """Fetch the content of a given page. You typically want to fetch the content of a page after you have received its URL from a search."""

    url: str


system = """You are a helpful research assistant. You can search the web and fetch content from URLs.
When tasked with a question, you will take as many steps and tries as needed to find the correct answer.
If you are doing a tool call, only respond with the tool call itself.
Do not respond with any reasoning or explanation in this case.
"""


@skill
def web_search(csi: Csi, input: Input) -> Output:
    """A Skill that can decide to search the web."""
    request = ChatRequest(
        model="llama-3.3-70b-instruct",
        messages=input.messages,
        system=system,
        tools=[Search, Fetch],
    )

    while True:
        response = request.chat(csi)
        if response.message.tool_calls:
            tool = response.message.tool_calls[0]
            params = (
                tool.parameters
                if isinstance(tool.parameters, dict)
                else tool.parameters.model_dump()
            )
            try:
                result = csi.invoke_tool(tool.name, **params)
            except ToolError as e:
                request.extend(ToolMessage(e.message))
            else:
                request.extend(ToolMessage(result.text()))
        else:
            break

    return Output(message=request.messages)
