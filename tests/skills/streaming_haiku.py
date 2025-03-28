from pydantic import BaseModel

from pharia_skill import ChatParams, Csi, Message
from pharia_skill.csi.inference import FinishReason
from pharia_skill.message_stream import message_stream
from pharia_skill.message_stream.response import (
    MessageAppend,
    MessageBegin,
    MessageEnd,
    Response,
)


class Input(BaseModel):
    root: str


class SkillOutput(BaseModel):
    finish_reason: FinishReason


@message_stream
def haiku_stream(csi: Csi, response: Response[None], input: Input) -> None:
    with csi._chat_stream(
        model="llama-3.1-8b-instruct",
        messages=[
            Message.system("You are a poet who strictly speask in haikus."),
            Message.user(input.root),
        ],
        params=ChatParams(),
    ) as chat_response:
        response.write(MessageBegin(chat_response.role))
        for event in chat_response.stream():
            response.write(MessageAppend(event.content))
        response.write(MessageEnd(None))
