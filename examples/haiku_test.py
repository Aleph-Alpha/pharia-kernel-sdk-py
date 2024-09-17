"""
An example of how to test skill code.
"""

from pharia_skill.testing import StubCsi

from .haiku import haiku


def test_haiku():
    topic = "oat milk"
    result = haiku(StubCsi, f'"{topic}"'.encode())
    assert "oat milk" in result.decode()
