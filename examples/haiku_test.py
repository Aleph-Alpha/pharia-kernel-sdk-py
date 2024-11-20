"""
An example of how to test skill code.
"""

from pharia_skill.testing import StubCsi

from .haiku import Input, Output, haiku


def test_haiku():
    input = Input(topic="oat milk")
    result = haiku(StubCsi(), input)
    assert isinstance(result, Output)
    assert "oat milk" in result.haiku
