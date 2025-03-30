"""
An example of how to test skill code.
"""

from pharia_skill import FinishReason
from pharia_skill.testing import MessageRecorder, StubCsi

from .haiku_stream import Input, SkillOutput, haiku_stream


def test_haiku_stream():
    # Given a haiku skill and a request about oat milk
    input = Input(topic="oat milk")

    # When executing the skill against a message recorder and a stub csi
    writer = MessageRecorder[SkillOutput]()
    haiku_stream(StubCsi(), writer, input)

    # Then the message recorded will be about oat milk
    first_message = writer.messages()[0]
    assert first_message.role == "assistant"
    assert "oat milk" in first_message.content
    assert first_message.payload is not None
    assert first_message.payload.finish_reason == FinishReason.STOP
