from pharia_skill.llama3 import Message


def test_message_render():
    message = Message.user("Hello, world!")
    expected = "<|start_header_id|>user<|end_header_id|>\n\nHello, world!<|eot_id|>"
    assert message.render() == expected
