from pydantic import BaseModel

from pharia_skill.llama3.message import (
    SystemMessage,
    ToolMessage,
    UserMessage,
)


def test_render_user_message():
    message = UserMessage("Hello, world!")
    expected = "<|start_header_id|>user<|end_header_id|>\n\nHello, world!<|eot_id|>"
    assert message.render() == expected


def test_render_system_message():
    message = SystemMessage("Hello, world!")
    expected = "<|start_header_id|>system<|end_header_id|>\n\nHello, world!<|eot_id|>"
    assert message.render() == expected


def deserialize_user_and_system_message():
    # Given a pydantic model with a list of either a user or system message
    class Either(BaseModel):
        messages: list[UserMessage | SystemMessage]

    # When deserializing a system message
    data = [
        {
            "role": "system",
            "content": "Hello, world!",
        },
        {
            "role": "user",
            "content": "Hello, world!",
        },
        {
            "role": "system",
            "content": "Hello, world!",
        },
    ]
    messages = Either.model_validate(data).messages

    # Then the messages are deserialized correctly
    assert isinstance(messages[0], SystemMessage)
    assert isinstance(messages[1], UserMessage)
    assert isinstance(messages[2], SystemMessage)


def test_tool_response_message_render():
    tool = ToolMessage(
        content='{"weather": "sunny", "temperature": "70 degrees"}',
        success=True,
    )
    expected = '<|start_header_id|>ipython<|end_header_id|>\n\ncompleted[stdout]{"weather": "sunny", "temperature": "70 degrees"}[/stdout]<|eot_id|>'
    assert tool.render() == expected


def test_failed_tool_response_message_render():
    tool = ToolMessage(
        content="failed to connect to server",
        success=False,
    )
    expected = "<|start_header_id|>ipython<|end_header_id|>\n\nfailed[stderr]failed to connect to server[/stderr]<|eot_id|>"
    assert tool.render() == expected
