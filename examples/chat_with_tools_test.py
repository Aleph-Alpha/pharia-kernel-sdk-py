import pytest

from pharia_skill import Csi
from pharia_skill.testing import DevCsi

from .chat_with_tools import Input, chat_with_tools


@pytest.fixture
def csi() -> Csi:
    return DevCsi()


def test_brave_search(csi: Csi):
    # Given a question
    question = "How many people live in Paris?"

    # When the skill is called
    input = Input(question=question)
    output = chat_with_tools(csi, input)

    # Then the answer is returned
    assert "90 million" in output.answer.lower()
