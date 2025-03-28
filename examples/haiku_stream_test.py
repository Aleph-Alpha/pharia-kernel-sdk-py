"""
An example of how to test skill code.
"""

from pharia_skill import MessageAppend
from pharia_skill.testing import MessageRecorder, StubCsi

from .haiku_stream import Input, SkillOutput, haiku_stream


def test_haiku_stream():
    input = Input(topic="oat milk")
    writer = MessageRecorder[SkillOutput]()
    haiku_stream(StubCsi(), writer, input)
    assert isinstance(writer.items[2], MessageAppend)
    assert "oat milk" in writer.items[2].text
