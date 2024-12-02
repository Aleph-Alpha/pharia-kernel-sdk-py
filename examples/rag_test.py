"""
An example of how to test skill code using a remote kernel
"""

from pharia_skill.testing import DevCsi

from .rag import Input, Output, answer_about_kernel


def test_answer_about_kernel():
    csi = DevCsi()
    input = Input(question="What is it?")
    result = answer_about_kernel(csi, input)
    assert isinstance(result, Output)
    assert "Kernel" in result.answer
    assert result.number_of_documents == 1
