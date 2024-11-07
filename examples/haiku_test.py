"""
An example of how to test skill code.
"""

from pharia_skill.testing import StubCsi

from .haiku import Input, haiku


def test_haiku():
    input = Input(topic="oat milk")
    result = haiku(StubCsi(), input)
    assert "oat milk" in result.completion
    assert "oat milk" in result.chat
