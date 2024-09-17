"""
An example of how to test skill code.
"""

import json

from pharia_skill.testing import StubCsi

from .haiku import haiku


def test_haiku():
    input = json.dumps({"topic": "oat milk"})
    result = haiku(StubCsi, input.encode())
    assert "oat milk" in result.decode()
