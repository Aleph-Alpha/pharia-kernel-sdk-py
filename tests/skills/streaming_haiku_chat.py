from pydantic import BaseModel
from pydantic.root_model import RootModel

from pharia_skill import ChatParams, Csi, FinishReason, Message
from pharia_skill.message_stream import message_stream
from pharia_skill.message_stream.writer import MessageWriter


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
    with csi._chat_stream(model, messages, params) as response:
        writer.forward_response(
            response, lambda r: SkillOutput(finish_reason=r.finish_reason())
        )
