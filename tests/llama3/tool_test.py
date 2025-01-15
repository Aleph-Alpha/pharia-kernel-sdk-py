import pytest
from pydantic import Field, ValidationError

from pharia_skill.llama3.response import Response
from pharia_skill.llama3.tool import (
    BraveSearch,
    CodeInterpreter,
    Tool,
    ToolCall,
    ToolResponse,
    WolframAlpha,
)


class GetGithubReadme(Tool):
    """Get the readme of a GitHub repository"""

    repository: str = Field(
        description="The name of the GitHub repository to get the readme from",
    )
    registry: str = "default"


def test_pydantic_tool_definition_for_function():
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
    assert tool_call.name == "brave_search"
    match tool_call.arguments:
        case BraveSearch(query=query):
            assert query == "current weather in Menlo Park, California"
        case _:
            assert False, "Expected BraveSearch"


def test_wolfram_alpha_call_is_parsed():
    # Given a response with a call to Wolfram Alpha
    raw = '<|python_tag|>wolfram_alpha.call(query="solve x^3 - 4x^2 + 6x - 24 = 0")<|eom_id|>'
    response = Response.from_raw(raw)

    # When parsing the tool call
    tool_call = ToolCall.from_response(response)

    # Then
    assert tool_call is not None
    assert tool_call.name == "wolfram_alpha"
    match tool_call.arguments:
        case WolframAlpha(query=query):
            assert query == "solve x^3 - 4x^2 + 6x - 24 = 0"
        case _:
            assert False, "Expected WolframAlpha"


def test_parse_function_call_from_response():
    response = """{"type": "function", "name": "get_github_readme", "parameters": {"repository": "pharia-kernel"}}"""

    tool_call = ToolCall.json_from_text(response)
    assert tool_call is not None
    assert isinstance(tool_call.arguments, dict)
    assert tool_call.arguments["repository"] == "pharia-kernel"


def test_json_function_call_render():
    response = '{"type": "function", "name": "get_github_readme", "parameters": {"repository": "pharia-kernel"}}'

    tool_call = ToolCall.json_from_text(response)
    assert tool_call is not None
    assert tool_call.render() == response


def test_render_tool_call_with_typed_args():
    response = '{"type": "function", "name": "get_github_readme", "parameters": {"repository": "pharia-kernel"}}'

    tool_call = ToolCall.json_from_text(response)
    assert tool_call is not None

    tool_call.try_parse([GetGithubReadme])
    assert isinstance(tool_call.arguments, GetGithubReadme)

    assert tool_call.render() == response


def test_code_interpreter_tool_call_render():
    tool_call = ToolCall(
        "code_interpreter",
        CodeInterpreter(src="def is_prime(n):\n   return True"),
    )
    assert tool_call.render() == "<|python_tag|>def is_prime(n):\n   return True"


def test_brave_search_tool_call_render():
    tool_call = ToolCall(
        "brave_search",
        BraveSearch(query="current weather in Menlo Park, California"),
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


def test_no_parsing_without_provided_tools():
    raw = ToolCall(
        name="get_github_readme",
        arguments={"repository": "pharia-kernel"},
    )
    raw.try_parse([])
    assert isinstance(raw.arguments, dict)


def test_no_parsing_for_wrong_tool():
    tools = [GetGithubReadme]
    raw = ToolCall(
        name="push_jira",
        arguments={"repository": "pharia-kernel"},
    )
    raw.try_parse(tools)
    assert isinstance(raw.arguments, dict)


def test_parsing_of_correct_tool():
    tools = [GetGithubReadme]
    raw = ToolCall(
        name="get_github_readme",
        arguments={"repository": "pharia-kernel"},
    )
    raw.try_parse(tools)
    assert isinstance(raw.arguments, GetGithubReadme)


def test_parsing_of_invalid_format_raises():
    tools = [GetGithubReadme]
    raw = ToolCall(
        name="get_github_readme",
        arguments={"whatever": "pharia-kernel"},
    )
    with pytest.raises(ValidationError):
        raw.try_parse(tools)
