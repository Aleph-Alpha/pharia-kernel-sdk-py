from pharia_skill.llama3 import Tool, ToolCall
from pharia_skill.llama3.response import Response


class GetGithubReadme(Tool):
    repository: str


def test_render_json_schema_tool_call():
    raw = '{"name": "get_github_readme", "parameters": {"repository": "pharia-kernel"}}'
    response = Response(raw, True)
    tool_call = ToolCall.from_response(response, tools=["get_github_readme"])

    assert tool_call is not None
    assert tool_call.name == "get_github_readme"
    assert isinstance(tool_call.parameters, dict)
    assert tool_call.render() == raw


def test_render_custom_parsed_tool_call():
    raw = '{"name": "get_github_readme", "parameters": {"repository": "pharia-kernel"}}'
    response = Response(raw, True)
    tool_call = ToolCall.from_response(response, tools=["get_github_readme"])
    assert tool_call is not None
    assert tool_call.name == GetGithubReadme.name()

    assert tool_call.render() == raw
