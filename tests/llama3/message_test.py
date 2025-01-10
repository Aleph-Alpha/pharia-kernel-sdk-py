from pharia_skill.llama3 import (
    BuiltInTool,
    Message,
    Role,
    ToolCall,
    ToolResponse,
)


def test_tool_call_message_render():
    tool_call = ToolCall(
        tool_name=BuiltInTool.BraveSearch,
        arguments={"query": "current weather in Menlo Park, California"},
    )
    message = Message(role=Role.Assistant, content=None, tool_call=tool_call)
    expected = '<|start_header_id|>assistant<|end_header_id|>\n\n<|python_tag|>brave_search.call(query="current weather in Menlo Park, California")<|eom_id|>'
    assert message.render() == expected


def test_tool_response_message_render():
    tool_response = ToolResponse(
        tool_name=BuiltInTool.BraveSearch,
        content='{"weather": "sunny", "temperature": "70 degrees"}',
        success=True,
    )
    message = Message(role=Role.IPython, content=None, tool_response=tool_response)
    expected = '<|start_header_id|>ipython<|end_header_id|>\n\ncompleted[stdout]{"weather": "sunny", "temperature": "70 degrees"}[/stdout]<|eot_id|>'
    assert message.render() == expected


def test_failed_tool_response_message_render():
    tool_response = ToolResponse(
        tool_name=BuiltInTool.BraveSearch,
        content="failed to connect to server",
        success=False,
    )
    message = Message(role=Role.IPython, content=None, tool_response=tool_response)
    expected = "<|start_header_id|>ipython<|end_header_id|>\n\nfailed[stderr]failed to connect to server[/stderr]<|eot_id|>"
    assert message.render() == expected


def test_message_from_raw_response():
    response = "Hello tim!<|eot_id|>"
    message = Message.from_raw_response(response)

    assert message.content == "Hello tim!"


def test_message_from_response_with_tool_call():
    response = "<|python_tag|>def is_prime(n):\n   return True<|eom_id|>"
    message = Message.from_raw_response(response)

    assert message.content is None
    assert message.tool_call is not None
    assert message.tool_call.tool_name == BuiltInTool.CodeInterpreter
    assert message.tool_call.arguments == {"code": "def is_prime(n):\n   return True"}


def test_message_tool_call_without_python_tag():
    """Llama3.3 does not prefix json tool calls with the python tag."""
    response = """{"type": "function", "name": "get_github_readme", "parameters": {"repository": "pharia-kernel"}}"""
    message = Message.from_raw_response(response)
    assert message.content is None
    assert message.tool_call is not None
    assert message.tool_call.tool_name == "get_github_readme"


def test_tool_call_from_chat_response_with_python_tag():
    response = """\n\n<|python_tag|>{"type": "function", "name": "get_github_readme", "parameters": {"repository": "pharia-kernel"}}"""
    message = Message.from_raw_response(response)
    assert message.content is None
    assert message.tool_call is not None
    assert message.tool_call.tool_name == "get_github_readme"
