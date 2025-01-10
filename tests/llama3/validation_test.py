import pytest

from pharia_skill.llama3 import Message, Role
from pharia_skill.llama3.request import validate_messages


def test_start_with_assistant():
    assistant = Message.assistant("You are a poet who strictly speaks in haikus.")
    user = Message.user("oat milk")

    with pytest.raises(ValueError):
        validate_messages([assistant, user])


def test_end_with_assistant():
    user = Message.user("oat milk")
    assistant = Message.assistant("You are a poet who strictly speaks in haikus.")

    with pytest.raises(ValueError):
        validate_messages([user, assistant])


def test_system_prompt_is_optional():
    system = Message.system("You are a poet who strictly speaks in haikus.")
    user = Message.user("oat milk")
    assistant = Message.assistant("Hello!")
    ipython = Message(role=Role.IPython, content="print('hello')")

    validate_messages([user, assistant, ipython])
    validate_messages([system, user, assistant, ipython])


def test_not_alternating_messages():
    user = Message.user("oat milk")
    ipython = Message(role=Role.IPython, content="print('hello')")

    with pytest.raises(ValueError):
        validate_messages([user, ipython])
