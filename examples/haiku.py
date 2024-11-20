from pydantic import BaseModel

from pharia_skill import ChatParams, Csi, Message, skill


class Input(BaseModel):
    topic: str


class Output(BaseModel):
    haiku: str


@skill
def haiku(csi: Csi, input: Input) -> Output:
    """A skill that generates haikus."""
    msg = Message.user(
        f"You are a poet who strictly speaks in haikus.\n\n{input.topic}"
    )
    answer = csi.chat("llama-3.1-8b-instruct", msg, ChatParams(max_tokens=64))
    return Output(haiku=answer.message.content.strip())
