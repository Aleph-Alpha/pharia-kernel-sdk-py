from pydantic import BaseModel, RootModel

from pharia_skill import CompletionParams, Csi
from pharia_skill.csi.inference import FinishReason
from pharia_skill.message_stream import message_stream
from pharia_skill.message_stream.response import (
    MessageAppend,
    MessageBegin,
    MessageEnd,
    Response,
)


class Input(RootModel[str]):
    root: str


class SkillOutput(BaseModel):
    finish_reason: FinishReason


@message_stream
def haiku_stream(csi: Csi, response: Response[SkillOutput], input: Input) -> None:
    with csi.completion_stream(
        model="llama-3.1-8b-instruct",
        prompt=f"Generate a haiku about {input.root}",
        params=CompletionParams(),
    ) as completion_response:
        response.write(MessageBegin(None))
        for event in completion_response.stream():
            response.write(MessageAppend(event.text))
        response.write(
            MessageEnd(SkillOutput(finish_reason=completion_response.finish_reason()))
        )
