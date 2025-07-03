from pydantic import BaseModel

from pharia_skill import Csi, Message, MessageWriter, message_stream


class Input(BaseModel):
    messages: list[Message]


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
    messages = [Message.system(SYSTEM), *input.messages]
    with csi.chat_stream_with_tools(
        model, messages, tools=["search", "fetch"]
    ) as response:
        writer.forward_response(response)
