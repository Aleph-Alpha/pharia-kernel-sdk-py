import pytest
from pydantic import BaseModel

from pharia_skill import Csi
from pharia_skill.message_stream import message_stream
from pharia_skill.message_stream.writer import (
    MessageAppend,
    MessageBegin,
    MessageEnd,
    MessageWriter,
    Reasoning,
)
from pharia_skill.testing import StubCsi
from pharia_skill.testing.dev.streaming_output import MessageRecorder, RecordedMessage


def test_message_recorder_can_be_used_to_test_skill_output():
    # Given a message stream skill
    class Input(BaseModel):
        pass

    @message_stream
    def my_skill(csi: Csi, writer: MessageWriter[None], input: Input) -> None:
        writer.begin_message("assistant")
        writer.append_to_message("The meaning of life")
        writer.end_message(payload=None)

    # When invoking it with the MessageRecorder
    csi = StubCsi()
    recorder = MessageRecorder[None]()
    my_skill(csi, recorder, Input())

    # Then the items can be read from the MessageRecorder
    assert recorder.items == [
        MessageBegin(role="assistant"),
        MessageAppend(text="The meaning of life"),
        MessageEnd(payload=None),
    ]


def test_starting_with_message_begin_is_valid():
    recorder = MessageRecorder[None]()
    recorder.write(MessageBegin(role="assistant"))

    assert recorder.messages() == [
        RecordedMessage(role="assistant", content="", payload=None),
    ]


def test_not_starting_with_message_begin_is_invalid():
    recorder = MessageRecorder[None]()
    with pytest.raises(ValueError):
        recorder.write(MessageAppend(text="The meaning of life"))


def test_message_append_can_follow_message_begin():
    recorder = MessageRecorder[None]()
    recorder.write(MessageBegin(role="assistant"))
    recorder.write(MessageAppend(text="The meaning of"))
    recorder.write(MessageAppend(text=" life"))
    assert recorder.messages() == [
        RecordedMessage(role="assistant", content="The meaning of life"),
    ]


def test_message_end_can_follow_message_append():
    class MyPayload(BaseModel):
        answer: int

    payload = MyPayload(answer=42)
    recorder = MessageRecorder[MyPayload]()
    recorder.write(MessageBegin(role="assistant"))
    recorder.write(MessageAppend(text="The meaning of"))
    recorder.write(MessageAppend(text=" life"))
    recorder.write(MessageEnd(payload=payload))

    assert recorder.messages() == [
        RecordedMessage(
            role="assistant",
            content="The meaning of life",
            payload=payload,
        ),
    ]


def test_message_begin_may_not_follow_message_begin():
    recorder = MessageRecorder[None]()
    recorder.write(MessageBegin(role="assistant"))

    with pytest.raises(ValueError):
        recorder.write(MessageBegin(role="assistant"))


def test_message_begin_may_not_follow_message_apped():
    recorder = MessageRecorder[None]()
    recorder.write(MessageBegin(role="assistant"))
    recorder.write(MessageAppend(text="The meaning of"))

    with pytest.raises(ValueError):
        recorder.write(MessageBegin(role="assistant"))


def test_consecutive_message_ends_are_invalid():
    recorder = MessageRecorder[None]()
    recorder.write(MessageBegin(role="assistant"))
    recorder.write(MessageEnd(payload=None))

    with pytest.raises(ValueError):
        recorder.write(MessageEnd(payload=None))


def test_message_recorder_json_output():
    # Given a message recorder
    recorder = MessageRecorder[None]()
    recorder.write(MessageBegin(role="assistant"))
    recorder.write(MessageAppend(text="The meaning of"))
    recorder.write(MessageAppend(text=" life"))
    recorder.write(MessageEnd(payload=None))

    # When creating a json output from the recorder
    output = recorder.skill_output()

    # Then the output is a list of json strings
    assert (
        output
        == '{"role":"assistant","content":"The meaning of life","reasoning_content":""}'
    )


def test_message_recorder_with_custom_payload_is_included_in_json():
    class MyPayload(BaseModel):
        answer: int

    recorder = MessageRecorder[MyPayload]()
    recorder.write(MessageBegin(role="assistant"))
    recorder.write(MessageAppend(text="The meaning of"))
    recorder.write(MessageAppend(text=" life"))
    recorder.write(MessageEnd(payload=MyPayload(answer=42)))

    assert (
        recorder.skill_output()
        == '{"role":"assistant","content":"The meaning of life","reasoning_content":"","payload":{"answer":42}}'
    )


def test_reasoning_content_is_accumulated():
    recorder = MessageRecorder[None]()
    recorder.write(MessageBegin(role="assistant"))
    recorder.write(Reasoning(content="Thinking..."))
    recorder.write(Reasoning(content="More thinking..."))
    recorder.write(MessageEnd(payload=None))
    assert recorder.messages() == [
        RecordedMessage(
            role="assistant",
            content="",
            reasoning_content="Thinking...More thinking...",
        )
    ]


def test_message_recorder_json_output_with_multiple_messages():
    # Given a message recorder
    recorder = MessageRecorder[None]()
    recorder.write(MessageBegin(role="assistant"))
    recorder.write(Reasoning(content="Thinking..."))
    recorder.write(MessageAppend(text="Hello!"))
    recorder.write(MessageEnd(payload=None))

    recorder.write(MessageBegin(role="assistant"))
    recorder.write(MessageAppend(text="Hi!"))
    recorder.write(MessageEnd(payload=None))

    # When creating a json output from the recorder
    output = recorder.skill_output()

    # Then the output is a list of json strings
    assert (
        output
        == '[{"role":"assistant","content":"Hello!","reasoning_content":"Thinking..."},{"role":"assistant","content":"Hi!","reasoning_content":""}]'
    )
