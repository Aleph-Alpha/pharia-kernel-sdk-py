from typing import Generator

import pytest
from pydantic import BaseModel

from pharia_skill import ChatParams, Csi, Message, message_stream
from pharia_skill.csi.inference import (
    ChatEvent,
    Role,
)
from pharia_skill.stream import MessageAppend, MessageBegin, MessageEnd
from pharia_skill.stream.chat_decorator import GeneratorWrapper, to_message_stream
from pharia_skill.testing import MessageRecorder, StubCsi


def test_generator_wrapper_stores_return_value():
    # given a generator that yields and returns
    def gen() -> Generator[int, None, int]:
        yield 1
        return 2

    # when we wrap it
    wrapper = GeneratorWrapper(gen())

    # Then we can iterate over the wrapper
    assert list(wrapper) == [1]

    assert wrapper.value == 2


def test_generator_wrapper_without_return_value():
    # given a generator that yields
    def gen() -> Generator[int, None, None]:
        yield 1

    wrapper = GeneratorWrapper(gen())
    assert list(wrapper) == [1]
    assert wrapper.value is None


def test_generator_wrapper_with_no_yield():
    # given a generator that yields
    def gen() -> int:
        return 2

    with pytest.raises(ValueError):
        GeneratorWrapper(gen())  # type: ignore


def test_haiku_stream_with_return():
    # Given a function written against the chat skill interface
    class HaikuInput(BaseModel):
        topic: str

    class HaikuOutput(BaseModel):
        anything: str

    def haiku_stream_with_return(
        csi: Csi, input: HaikuInput
    ) -> Generator[ChatEvent, None, HaikuOutput]:
        model = "llama-3.1-8b-instruct"
        messages = [
            Message.system("You are a poet who strictly speaks in haikus."),
            Message.user(input.topic),
        ]
        params = ChatParams()
        with csi.chat_stream(model, messages, params) as response:
            yield from response.message()

        return HaikuOutput(anything="anything")

    # When transforming it to a message stream skill
    skill = message_stream(to_message_stream(haiku_stream_with_return))

    # Then it can be invoked with the MessageWriter and StubCsi
    csi = StubCsi()
    writer = MessageRecorder[HaikuOutput]()
    skill(csi, writer, HaikuInput(topic="The meaning of life"))

    # And the messages are recorded
    assert writer.items == [
        MessageBegin(role=Role.System),
        MessageAppend(
            text="You are a poet who strictly speaks in haikus.",
        ),
        MessageAppend(
            text="The meaning of life",
        ),
        MessageEnd(payload=HaikuOutput(anything="anything")),
    ]
