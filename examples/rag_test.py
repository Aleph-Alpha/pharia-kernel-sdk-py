"""
An example of how to test skill code using a remote kernel
"""

import pytest

from pharia_skill.testing import DevCsi

from .rag import Input, Output, answer_about_heidelberg


@pytest.mark.kernel
def test_answer_about_heidelberg():
    csi = DevCsi()
    input = Input(question="What is the population?")
    result = answer_about_heidelberg(csi, input)
    assert isinstance(result, Output)
    assert "Heidelberg" in result.answer
    assert result.number_of_documents > 1
