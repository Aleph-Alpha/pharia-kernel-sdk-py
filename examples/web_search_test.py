import pytest

from pharia_skill import Message
from pharia_skill.testing import DevCsi, MessageRecorder

from .web_search import Input, web_search


@pytest.mark.skip("Search and fetch tools are not always configured.")
def test_skill_searches_the_web():
    csi = DevCsi(namespace="playground", project="kernel-test")

    # Given a question that can only be answered by searching the web
    query = "What was the winning time of the 21st stage of the 2025 Giro de Italia?"
    input = Input(messages=[Message.user(query)])

    # When the skill is called
    recorder: MessageRecorder[None] = MessageRecorder()
    web_search(csi, recorder, input)

    # Then the correct answer is given
    messages = recorder.messages()

    assert len(messages) == 1
    answer = messages[0].content
    assert "3:12:19" in answer.lower()
