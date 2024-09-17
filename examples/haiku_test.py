"""
An example of how to test skill code.
"""

from pharia_skill.testing import StubCsi

from .haiku import MyModel, haiku


def test_haiku():
    input = MyModel(topic="oat milk")
    result = haiku(StubCsi, input)
    assert "oat milk" in result.decode()
