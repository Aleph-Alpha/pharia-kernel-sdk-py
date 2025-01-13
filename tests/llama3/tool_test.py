from pydantic import Field

from pharia_skill.llama3.response import Response
from pharia_skill.llama3.tool import (
    BuiltInTool,
    Tool,
    ToolCall,
    ToolResponse,
)


def test_pydantic_tool_definition_for_function():
    class GetGithubReadme(Tool):
        """Get the readme of a GitHub repository"""

        repository: str = Field(
            description="The name of the GitHub repository to get the readme from",
        )
        registry: str = "default"

    expected = {
        "type": "function",
        "function": {
            "name": "get_github_readme",
            "description": "Get the readme of a GitHub repository",
            "parameters": {
                "type": "object",
                "required": ["repository"],
                "properties": {
                    "repository": {
                        "type": "string",
                        "description": "The name of the GitHub repository to get the readme from",
                    },
                    "registry": {
                        "type": "string",
                        "default": "default",
                    },
                },
            },
        },
    }
    assert GetGithubReadme.render() == expected


def test_brave_search_call_is_parsed():
    # Given a response with a call to Brave Search
    raw = '<|python_tag|>brave_search.call(query="current weather in Menlo Park, California")<|eom_id|>'
    response = Response.from_raw(raw)

    # When parsing the tool call
    tool_call = ToolCall.from_response(response)

    # Then
    assert tool_call is not None
    assert tool_call.name == BuiltInTool.BraveSearch
    assert tool_call.arguments == {"query": "current weather in Menlo Park, California"}


def test_wolfram_alpha_call_is_parsed():
    # Given a response with a call to Wolfram Alpha
    raw = '<|python_tag|>wolfram_alpha.call(query="solve x^3 - 4x^2 + 6x - 24 = 0")<|eom_id|>'
    response = Response.from_raw(raw)

    # When parsing the tool call
    tool_call = ToolCall.from_response(response)

    # Then
    assert tool_call is not None
    assert tool_call.name == BuiltInTool.WolframAlpha
    assert tool_call.arguments == {"query": "solve x^3 - 4x^2 + 6x - 24 = 0"}


def test_parse_function_call_from_response():
    response = """{"type": "function", "name": "get_github_readme", "parameters": {"repository": "pharia-kernel"}}"""

    tool_call = ToolCall.json_from_text(response)
    assert tool_call is not None
    assert tool_call.arguments["repository"] == "pharia-kernel"


def test_json_function_call_render():
    response = '{"type": "function", "name": "get_github_readme", "parameters": {"repository": "pharia-kernel"}}'

    tool_call = ToolCall.json_from_text(response)
    assert tool_call is not None
    assert tool_call.render_json() == response


def test_code_interpreter_tool_call_render():
    tool_call = ToolCall(
        name=BuiltInTool.CodeInterpreter,
        arguments={"code": "def is_prime(n):\n   return True"},
    )
    assert tool_call.render() == "<|python_tag|>def is_prime(n):\n   return True"


def test_brave_search_tool_call_render():
    tool_call = ToolCall(
        name=BuiltInTool.BraveSearch,
        arguments={"query": "current weather in Menlo Park, California"},
    )
    expected = '<|python_tag|>brave_search.call(query="current weather in Menlo Park, California")'
    assert tool_call.render() == expected


def test_tool_response_message_render():
    tool = ToolResponse(
        content='{"weather": "sunny", "temperature": "70 degrees"}',
        success=True,
    )
    expected = '<|start_header_id|>ipython<|end_header_id|>\n\ncompleted[stdout]{"weather": "sunny", "temperature": "70 degrees"}[/stdout]<|eot_id|>'
    assert tool.render() == expected


def test_failed_tool_response_message_render():
    tool = ToolResponse(
        content="failed to connect to server",
        success=False,
    )
    expected = "<|start_header_id|>ipython<|end_header_id|>\n\nfailed[stderr]failed to connect to server[/stderr]<|eot_id|>"
    assert tool.render() == expected
