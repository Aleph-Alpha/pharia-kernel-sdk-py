import inspect
from types import GeneratorType
from typing import Any, Callable, Generator, TypeVar

import pytest
from pydantic import BaseModel

from pharia_skill import ChatParams, Csi, Message, message_stream
from pharia_skill.csi.inference import (
    ChatEvent,
    FinishReason,
    MessageAppend,
    MessageBegin,
    TokenUsage,
)
from pharia_skill.message_stream import MessageAppend as WriterMessageAppend
from pharia_skill.message_stream import MessageEnd as WriterMessageEnd
from pharia_skill.message_stream.writer import MessageWriter
from pharia_skill.testing import MessageRecorder, StubCsi

Input = TypeVar("Input", bound=BaseModel)
Output = TypeVar("Output", bound=BaseModel)


def chat(
    func: Callable[[Csi, Input], Generator[ChatEvent, None, Output | None]],
) -> Callable[[Csi, Input], Generator[ChatEvent, None, Output | None]]:
    """Turn a generator into a Skill that streams it outputs.

    This decorator offers a different interface than @message_stream.
    While @message_stream injects a `MessageWriter` that you can use to write
    intermediate results to, this decorator lets you write a generator that yields
    intermediate results and optionally returns a result.

    The decorated function must be a typed generator function. It must have exactly two arguments.
    The first argument must be of type `Csi` and the second argument must be a Pydantic model.
    The items type of the generator must be a `ChatEvent`. The return type must be a Pydantic model or `None`.

    Example::

        @chat
        def haiku_stream(csi: Csi, input: HaikuInput) -> Generator[ChatEvent, None, HaikuOutput]:
            model = "llama-3.1-8b-instruct"
            messages = [
                Message.system("You are a poet who strictly speaks in haikus."),
                Message.user(input.topic),
            ]
            params = ChatParams()
            with csi.chat_stream(model, messages, params) as response:
                yield from response.stream()

            return HaikuOutput(anything="anything")
    """
    message_stream(to_message_stream(func))
    return func


def to_message_stream(
    func: Callable[[Csi, Input], Generator[ChatEvent, None, Output | None]],
) -> Callable[[Csi, MessageWriter[Output], Input], None]:
    """Convert a chat skill a user would write to a function that can be decorated with @message_stream.

    Having this separated from the decorator allows for easier testing of the generated function.
    """

    signature = list(inspect.signature(func).parameters.values())
    assert len(signature) == 2, "Chat Skills must have exactly two arguments."

    input_model = signature[1].annotation
    assert isinstance(input_model, type) and issubclass(input_model, BaseModel), (
        "The second argument must be a Pydantic model, found: " + str(input_model)
    )

    def inner(csi: Csi, writer: MessageWriter[Output], input: input_model) -> None:  # type: ignore
        try:
            wrapper = GeneratorWrapper(func(csi, input))
        except ValueError:
            raise ValueError(
                "A Skill decorated with @chat must be a generator. ",
                "Make sure to yield from your Skill, otherwise you should use the @skill decorator.",
            )
        for event in wrapper:
            match event:
                case MessageBegin(role):
                    writer.begin_message(role)
                case MessageAppend(content):
                    writer.append_to_message(content)
                case FinishReason(), TokenUsage():
                    # This decorator is opinionated: If you use it, you "simply" want to stream a single completion.
                    # The caller does not get to see the token usage or the finish reason.
                    pass
                case _:
                    raise ValueError(
                        f"Yielded unexpected event of type {type(event)} in the @chat decorator. "
                        f"The @chat decorator only supports MessageBegin, MessageAppend, FinishReason, and TokenUsage events, got: {event}"
                    )

        # Write the return message of the function
        writer.end_message(wrapper.value)

    return inner


class GeneratorWrapper:
    """Helps to extract the return value of a generator.

    See https://peps.python.org/pep-0380/#use-of-stopiteration-to-return-values
    """

    def __init__(self, gen: Generator[Any, None, Any]):
        if not isinstance(gen, GeneratorType):
            raise ValueError
        self.gen = gen

    def __iter__(self):
        self.value = yield from self.gen
        return self.value


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
            yield from response.stream()

        return HaikuOutput(anything="anything")

    # When transforming it to a message stream skill
    skill = message_stream(to_message_stream(haiku_stream_with_return))

    # Then it can be invoked with the MessageWriter and StubCsi
    csi = StubCsi()
    writer = MessageRecorder[HaikuOutput]()
    skill(csi, writer, HaikuInput(topic="The meaning of life"))

    # And the messages are recorded
    assert writer.items == [
        WriterMessageAppend(
            text="You are a poet who strictly speaks in haikus.",
        ),
        WriterMessageAppend(
            text="The meaning of life",
        ),
        WriterMessageEnd(payload=HaikuOutput(anything="anything")),
    ]
