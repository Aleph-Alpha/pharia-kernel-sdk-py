from pharia_skill.llama3 import SystemMessage, UserMessage


def test_render_user_message():
    message = UserMessage("Hello, world!")
    expected = "<|start_header_id|>user<|end_header_id|>\n\nHello, world!<|eot_id|>"
    assert message.render() == expected


def test_render_system_message():
    message = SystemMessage("Hello, world!")
    expected = "<|start_header_id|>system<|end_header_id|>\n\nHello, world!<|eot_id|>"
    assert message.render() == expected
