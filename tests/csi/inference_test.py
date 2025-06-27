from pydantic import BaseModel

from pharia_skill.csi.inference import Message
from pharia_skill.csi.inference_types import Logprob


def test_serialized_roles_are_openai_compatible():
    class ChatInterface(BaseModel):
        messages: list[Message]

    message = Message.user("Hello, world!")
    input = ChatInterface(messages=[message])
    expected = '{"messages":[{"role":"user","content":"Hello, world!"}]}'
    assert input.model_dump_json() == expected


def test_logbprob_try_as_utf8():
    logprob = Logprob(token=b"Hi", logprob=1.0)
    assert logprob.try_as_utf8() == "Hi"


def test_logbprob_try_as_utf8_returns_none_for_invalid_utf8():
    logprob = Logprob(token=b"\x80", logprob=1.0)
    assert logprob.try_as_utf8() is None
