from collections.abc import Generator

from pydantic import BaseModel

from pharia_skill import (
    ChatEvent,
    ChatParams,
    Csi,
    Message,
    chat,
)


class Input(BaseModel):
    topic: str


class Output(BaseModel):
    summary: str


@chat
def haiku_stream(csi: Csi, input: Input) -> Generator[ChatEvent, None, Output]:
    """A skill that streams a haiku."""
    model = "llama-3.1-8b-instruct"
    messages = [
        Message.system("You are a poet who strictly speaks in haikus."),
        Message.user(input.topic),
    ]
    params = ChatParams()
    with csi.chat_stream(model, messages, params) as response:
        yield from response.message()

    return Output(summary=f"A haiku about {input.topic}.")
