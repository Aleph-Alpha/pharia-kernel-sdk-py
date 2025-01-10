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
        status="success",
        content='{"weather": "sunny", "temperature": "70 degrees"}',
    )
    message = Message(role=Role.IPython, content=None, tool_response=tool_response)
    expected = '<|start_header_id|>ipython<|end_header_id|>\n\ncompleted[stdout]{"weather": "sunny", "temperature": "70 degrees"}[/stdout]<|eot_id|>'
    assert message.render() == expected


def test_failed_tool_response_message_render():
    tool_response = ToolResponse(
        tool_name=BuiltInTool.BraveSearch,
        status="failure",
        content="failed to connect to server",
    )
    message = Message(role=Role.IPython, content=None, tool_response=tool_response)
    expected = "<|start_header_id|>ipython<|end_header_id|>\n\nfailed[stderr]failed to connect to server[/stderr]<|eot_id|>"
    assert message.render() == expected
