from pharia_skill.llama3 import (
    BuiltInTool,
    Message,
    Role,
    ToolResponse,
)


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
