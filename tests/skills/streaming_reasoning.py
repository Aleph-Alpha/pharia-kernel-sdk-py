from pydantic import BaseModel, RootModel

from pharia_skill.csi.csi import Csi
from pharia_skill.csi.inference.types import FinishReason
from pharia_skill.message_stream import message_stream
from pharia_skill.message_stream.writer import MessageWriter


class Input(RootModel[str]):
    root: str


class SkillOutput(BaseModel):
    finish_reason: FinishReason


@message_stream
def reasoning_stream(
    _csi: Csi, writer: MessageWriter[SkillOutput], input: Input
) -> None:
    """A skill that streams a chat response with reasoning content.

    It does not depend on a Csi so it does not depend on a model with reasoning capabilities.
    """
    writer.begin_message(role="assistant")
    writer.append_to_reasoning(f"I am thinking about the question: {input.root}")
    writer.append_to_reasoning("I think the meaning of life is 42.")
    writer.append_to_message("So the answer is 42.")
    writer.end_message(payload=SkillOutput(finish_reason=FinishReason.STOP))
