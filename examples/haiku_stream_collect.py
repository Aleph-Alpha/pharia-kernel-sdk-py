from pydantic import BaseModel

from pharia_skill import (
    ChatParams,
    Csi,
    Message,
    MessageWriter,
    message_stream,
)


class Input(BaseModel):
    topic: str


class SkillOutput(BaseModel):
    content: str


@message_stream
def haiku_stream(csi: Csi, writer: MessageWriter[SkillOutput], input: Input) -> None:
    """A skill that streams a haiku."""
    model = "llama-3.1-8b-instruct"
    messages = [
        Message.system("You are a poet who strictly speaks in haikus."),
        Message.user(input.topic),
    ]
    params = ChatParams()
    content = ""
    with csi._chat_stream(model, messages, params) as response:
        writer.begin_message(response.role)
        for event in response.stream():
            content += event.content
            writer.append_to_message(event.content)
    writer.end_message(SkillOutput(content=content))
