from pydantic import BaseModel
from pydantic.root_model import RootModel

from pharia_skill import ChatParams, Csi, Message
from pharia_skill.csi.inference import FinishReason
from pharia_skill.stream import message_stream
from pharia_skill.stream.writer import (
    MessageWriter,
)


class Input(RootModel[str]):
    root: str


class SkillOutput(BaseModel):
    finish_reason: FinishReason


@message_stream
def haiku_stream(csi: Csi, writer: MessageWriter[SkillOutput], input: Input) -> None:
    model = "llama-3.1-8b-instruct"
    messages = [
        Message.system("You are a poet who strictly speaks in haikus."),
        Message.user(input.root),
    ]
    params = ChatParams()
    with csi.chat_stream(model, messages, params) as response:
        writer.begin_message(response.role)
        for event in response.stream():
            writer.append_to_message(event.content)
        writer.end_message(SkillOutput(finish_reason=response.finish_reason()))
