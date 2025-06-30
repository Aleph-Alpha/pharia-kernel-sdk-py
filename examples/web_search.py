from pydantic import BaseModel

from pharia_skill import ChatSession, Csi, MessageWriter, message_stream
from pharia_skill.csi.tool import ToolCallRequest


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
    session = ChatSession(csi, model, SYSTEM, ["search", "fetch"])
    response = session.ask(input.question)

    while True:
        if isinstance(response, ToolCallRequest):
            tool_response = csi.invoke_tool(response.name, **response.parameters)
            response = session.report_tool_result(tool_response)
        else:
            writer.begin_message(role="assistant")
            for append in response:
                writer.append_to_message(append.content)
            writer.end_message()
            break
