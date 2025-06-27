from pydantic import BaseModel

from pharia_skill import Csi, Message, MessageWriter, message_stream
from pharia_skill.csi.inference_types import MessageAppend
from pharia_skill.csi.tool import ToolCall


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

    messages = [Message.system(SYSTEM)] + input.messages
    model = "llama-3.3-70b-instruct"

    while True:
        response = csi.chat_stream(model, messages, tools=["search", "fetch"])
        stream = response.stream_with_tool()
        first_chunk = next(stream)

        if isinstance(first_chunk, ToolCall):
            # TODO chat stream should validate alternation between assistant and user/tool
            # Make it part of the message history
            tool_call_request = Message.assistant(first_chunk.render())
            messages.append(tool_call_request)

            tool_response = csi.invoke_tool(first_chunk.name, **first_chunk.parameters)
            rendered = (
                f'completed[stdout]:{{"result": {tool_response.text()}}}[/stdout]'
            )
            # We need a concept for tool responses as messages now
            messages.append(Message.tool(rendered))
        else:
            writer.begin_message()
            writer.append_to_message(first_chunk.content)

            # We do not account for the possibility of getting two tool calls
            for chunk in stream:
                assert isinstance(chunk, MessageAppend)
                writer.append_to_message(chunk.content)
            return
