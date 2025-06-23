from pydantic import BaseModel, RootModel

from pharia_skill import CompletionParams, Csi
from pharia_skill.csi.inference import FinishReason
from pharia_skill.message_stream import message_stream
from pharia_skill.message_stream.writer import (
    MessageWriter,
)


class Input(RootModel[str]):
    root: str


class SkillOutput(BaseModel):
    finish_reason: FinishReason


@message_stream
def haiku_stream(csi: Csi, writer: MessageWriter[SkillOutput], input: Input) -> None:
    model = "llama-3.1-8b-instruct"
    prompt = f"Generate a haiku about {input.root}"
    params = CompletionParams(max_tokens=50)
    with csi._completion_stream(model, prompt, params) as response:
        writer.forward_response(
            response, lambda r: SkillOutput(finish_reason=r.finish_reason())
        )
