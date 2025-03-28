from pydantic import BaseModel, RootModel

from pharia_skill import CompletionParams, Csi
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
    prompt = f"Generate a haiku about {input.root}"
    params = CompletionParams(max_tokens=50)
    with csi.completion_stream(model, prompt, params) as response:
        writer.begin_message()
        for event in response.stream():
            writer.append_to_message(event.text)
        writer.end_message(SkillOutput(finish_reason=response.finish_reason()))
