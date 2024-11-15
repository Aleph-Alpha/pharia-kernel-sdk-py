"""
An example of how to test skill code using a remote kernel
"""

import pytest

from pharia_skill import Csi
from pharia_skill.testing import DevCsi

from .heidelberg import Input, Output, heidelberg


@pytest.fixture
def csi() -> Csi:
    # you have to make sure that a Pharia Kernel instance is available
    return DevCsi()


# you can remove that mark in your code, it is to prevent the test to run on github ci
@pytest.mark.kernel
def test_heidelberg(csi: Csi):
    input = Input(question="What is the population?")
    result = heidelberg(csi, input)
    assert isinstance(result, Output)
    assert "Heidelberg" in result.answer
    assert result.number_of_documents > 1
