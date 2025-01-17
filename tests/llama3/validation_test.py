import pytest

from pharia_skill.llama3 import (
    SystemMessage,
    ToolMessage,
    UserMessage,
)
from pharia_skill.llama3.message import AssistantMessage
from pharia_skill.llama3.request import validate_messages


def test_start_with_assistant():
    assistant = AssistantMessage(
        content="You are a poet who strictly speaks in haikus.",
    )
    user = UserMessage("oat milk")

    with pytest.raises(ValueError):
        validate_messages([assistant, user])


def test_end_with_assistant():
    user = UserMessage("oat milk")
    assistant = AssistantMessage(
        content="You are a poet who strictly speaks in haikus.",
    )

    with pytest.raises(ValueError):
        validate_messages([user, assistant])


def test_system_prompt_is_optional():
    system = SystemMessage("You are a poet who strictly speaks in haikus.")
    user = UserMessage("oat milk")
    assistant = AssistantMessage(content="Hello!")
    ipython = ToolMessage("print('hello')")

    validate_messages([user, assistant, ipython])
    validate_messages([system, user, assistant, ipython])


def test_not_alternating_messages():
    user = UserMessage("oat milk")
    ipython = ToolMessage("print('hello')")

    with pytest.raises(ValueError):
        validate_messages([user, ipython])
