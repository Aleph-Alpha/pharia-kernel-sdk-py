"""
An example of how to test skill code using a remote kernel
"""

from pharia_skill.testing import DevCsi

from .rag import Input, Output, answer_about_kernel


def test_answer_about_kernel():
    # Given a question about if the Kernel is related to fishing
    csi = DevCsi()
    input = Input(question="Is the Kernel related to fishing?")

    # When
    result = answer_about_kernel(csi, input)
    assert isinstance(result, Output)

    # Then it should, based on the document, mention the word "fishermen"
    assert "fishermen" in result.answer
    assert result.number_of_documents >= 1
