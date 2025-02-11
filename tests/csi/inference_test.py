from pydantic import BaseModel

from pharia_skill.csi.inference import Logprob, Message


def test_serialized_roles_are_openai_compatible():
    class ChatInterface(BaseModel):
        messages: list[Message]

    message = Message.user("Hello, world!")
    input = ChatInterface(messages=[message])
    expected = '{"messages":[{"role":"user","content":"Hello, world!"}]}'
    assert input.model_dump_json() == expected


def test_logbprob_try_as_utf8():
    logprob = Logprob(token=[72, 105], logprob=1.0)
    assert logprob.try_as_utf8() == "Hi"


def test_logbprob_try_as_utf8_returns_none_for_invalid_utf8():
    logprob = Logprob(token=[128], logprob=1.0)
    assert logprob.try_as_utf8() is None
