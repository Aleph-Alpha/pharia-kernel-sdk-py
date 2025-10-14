from pydantic import BaseModel

from pharia_skill import Csi, FinishReason, Message, MessageWriter, message_stream


class Input(BaseModel):
    topic: str
    model: str = "llama-3.1-8b-instruct"


class SkillOutput(BaseModel):
    finish_reason: FinishReason


@message_stream
def haiku_stream(csi: Csi, writer: MessageWriter[SkillOutput], input: Input) -> None:
    """A skill that streams a haiku."""
    messages = [
        Message.system("You are a poet who strictly speaks in haikus."),
        Message.user(input.topic),
    ]
    with csi.chat_stream(input.model, messages) as response:
        writer.forward_response(
            response, lambda r: SkillOutput(finish_reason=r.finish_reason())
        )
