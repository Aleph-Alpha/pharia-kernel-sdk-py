from collections.abc import Generator

from pydantic import BaseModel

from pharia_skill import Csi, Message, MessageWriter, message_stream
from pharia_skill.csi.inference_types import MessageAppend
from pharia_skill.csi.tool import ToolCallRequest, ToolOutput


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
    response = session.chat(input.question)

    while True:
        if isinstance(response, ToolCallRequest):
            # TODO chat stream should validate alternation between assistant and user/tool
            tool_response = csi.invoke_tool(response.name, **response.parameters)
            response = session.report_tool_result(tool_response)
        else:
            writer.begin_message()

            # We do not account for the possibility of getting two tool calls
            for chunk in response:
                assert isinstance(chunk, MessageAppend)
                writer.append_to_message(chunk.content)
            return


class ChatSession:
    def __init__(
        self,
        csi: Csi,
        model: str,
        system: str | None = None,
        tools: list[str] | None = None,
    ):
        self.csi = csi
        self.model = model
        self.messages: list[Message] = [Message.system(system)] if system else []
        self.tools = tools

    def reply(
        self, message: Message
    ) -> Generator[MessageAppend, None, None] | ToolCallRequest:
        self.messages.append(message)
        response = self.csi.chat_stream(self.model, self.messages, tools=self.tools)
        stream = response.stream_with_tool()
        if isinstance(stream, ToolCallRequest):
            self.messages.append(stream._as_message())
        return stream

    def chat(
        self, question: str
    ) -> Generator[MessageAppend, None, None] | ToolCallRequest:
        return self.reply(Message.user(question))

    def report_tool_result(
        self, tool_result: ToolOutput
    ) -> Generator[MessageAppend, None, None] | ToolCallRequest:
        return self.reply(tool_result._as_message())
