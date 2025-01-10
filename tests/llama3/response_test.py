from pharia_skill.llama3.response import Response


def test_response_from_raw():
    raw = "\n\nprint('Hello, World!')<|eom_id|>"

    parsed = Response.from_raw(raw)
    assert parsed.text == "print('Hello, World!')"
    assert not parsed.python_tag


def test_response_with_python_tag_from_raw():
    raw = "\n\n<|python_tag|>print('Hello, World!')<|eom_id|>"

    parsed = Response.from_raw(raw)
    assert parsed.text == "print('Hello, World!')"
    assert parsed.python_tag
