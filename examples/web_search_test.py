import pytest

from pharia_skill.llama3 import AssistantMessage, UserMessage
from pharia_skill.testing import DevCsi

from .web_search import Input, web_search


@pytest.mark.skip("Search and fetch tools are not always configured.")
def test_skill_searches_the_web():
    csi = DevCsi(namespace="playground", project="kernel-test")

    # Given a question that can only be answered by searching the web
    query = "What was the winning time of the last stage of the 2025 Giro de Italia?"
    input = Input(messages=[UserMessage(content=query)])

    # When the skill is called
    result = web_search(csi, input)

    # Then the correct answer is given
    answer = result.message[-1]
    assert isinstance(answer, AssistantMessage)
    assert answer.content is not None
    assert "3:12:19" in answer.content.lower()
