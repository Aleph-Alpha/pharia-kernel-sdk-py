from pydantic import BaseModel

from pharia_skill import ChatSession, Csi, MessageWriter, message_stream
from pharia_skill.csi.inference import ChatStreamResponse


class Input(BaseModel):
    question: str


SYSTEM = """You are a helpful research assistant.
When tasked with a question, you will take as many steps and tries as needed to find the correct answer.
If you are doing a tool call, only respond with the tool call itself.
Do not respond with any reasoning or explanation in this case.

You can search the web and fetch content from URLs. Use markdown content when fetching URLs.
To ensure that efficiency, only fetch the content after you have found the relevant URLs."""


@message_stream
def web_search(csi: Csi, writer: MessageWriter[None], input: Input) -> None:
    """A Skill that can decide to search the web."""

    model = "llama-3.3-70b-instruct"
    agent = Agent(model, SYSTEM, ["search", "fetch"])
    response = agent.run(csi, input.question)
    writer.forward_response(response)


class Agent:
    def __init__(self, model: str, system: str, tools: list[str]):
        self.model = model
        self.system = system
        self.tools = tools

    def run(self, csi: Csi, question: str) -> ChatStreamResponse:
        session = ChatSession(csi, self.model, self.system, self.tools)
        response = session.ask(question)
        while True:
            if (tool_call := response.tool_call()) is not None:
                tool_response = csi.invoke_tool(tool_call.name, **tool_call.parameters)
                response = session.report_tool_result(tool_response)
            else:
                return response
