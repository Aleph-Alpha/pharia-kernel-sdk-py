import pytest

from pharia_skill import Csi
from pharia_skill.testing import DevCsi

from .brave_search import Input, brave_search


@pytest.fixture
def csi() -> Csi:
    return DevCsi()


def test_brave_search(csi: Csi):
    # Given a question
    question = "How many people live in Paris?"

    # When the skill is called
    input = Input(question=question)
    output = brave_search(csi, input)

    # Then the answer is returned
    assert "90 million" in output.answer.lower()
