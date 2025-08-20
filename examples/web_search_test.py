import pytest

from pharia_skill import AgentInput, AgentMessage
from pharia_skill.testing import DevCsi, MessageRecorder

from .web_search import web_search


@pytest.mark.skip(reason="No Kernel set up with MCP tools in CI")
def test_skill_searches_the_web():
    csi = DevCsi(namespace="playground", project="kernel-test")

    # Given a question that can only be answered by searching the web
    query = "Who won the 2025 Giro de Italia?"
    input = AgentInput(messages=[AgentMessage(role="user", content=query)])

    # When the skill is called
    recorder: MessageRecorder[None] = MessageRecorder()
    web_search(csi, recorder, input)

    # Then the correct answer is given
    messages = recorder.messages()

    assert len(messages) == 1
    answer = messages[0].content
    assert "simon yates" in answer.lower(), answer
