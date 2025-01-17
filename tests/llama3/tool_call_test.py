import pytest
from pydantic import ValidationError

from pharia_skill.llama3 import (
    BraveSearch,
    CodeInterpreter,
    JsonSchema,
    Tool,
    ToolCall,
    WolframAlpha,
)
from pharia_skill.llama3.response import Response
from pharia_skill.llama3.tool import Function


class GetGithubReadme(Tool):
    repository: str


def test_render_json_schema_tool_call():
    raw = '{"name": "get_github_readme", "parameters": {"repository": "pharia-kernel"}}'
    response = Response(raw, True)
    tool = JsonSchema(
        function=Function(
            name="get_github_readme", parameters={"repository": "pharia-kernel"}
        )
    )
    tool_call = ToolCall.from_response(response, tools=[tool])

    assert tool_call is not None
    assert tool_call.name == "get_github_readme"
    assert isinstance(tool_call.parameters, dict)
    assert tool_call.render() == raw


def test_render_custom_parsed_tool_call():
    raw = '{"name": "get_github_readme", "parameters": {"repository": "pharia-kernel"}}'
    response = Response(raw, True)
    tool_call = ToolCall.from_response(response, tools=[GetGithubReadme])
    assert tool_call is not None
    assert isinstance(tool_call.parameters, GetGithubReadme)

    assert tool_call.render() == raw


def test_brave_search_call_is_parsed():
    # Given a response with a call to Brave Search
    raw = 'brave_search.call(query="current weather in Menlo Park, California")'
    response = Response(raw, True)

    # When parsing the tool call
    tool_call = ToolCall.from_response(response, tools=[BraveSearch])

    # Then
    assert tool_call is not None
    assert isinstance(tool_call.parameters, BraveSearch)
    assert tool_call.parameters.query == "current weather in Menlo Park, California"
    assert tool_call.render() == raw


def test_wolfram_alpha_call_is_parsed():
    # Given a response with a call to Wolfram Alpha
    raw = 'wolfram_alpha.call(query="solve x^3 - 4x^2 + 6x - 24 = 0")'
    response = Response(raw, True)

    # When parsing the tool call
    tool_call = ToolCall.from_response(response, tools=[WolframAlpha])

    # Then
    assert tool_call is not None
    assert isinstance(tool_call.parameters, WolframAlpha)
    assert tool_call.parameters.query == "solve x^3 - 4x^2 + 6x - 24 = 0"
    assert tool_call.render() == raw


def test_code_interpreter_tool_call_render():
    raw = "def is_prime(n):\\n   return True"
    response = Response(raw, True)
    tool_call = ToolCall.from_response(response, tools=[CodeInterpreter])
    assert tool_call is not None
    assert isinstance(tool_call.parameters, CodeInterpreter)
    assert tool_call.render() == raw


def test_no_parsing_without_provided_tools():
    raw = "def is_prime(n):\\n   return True"
    response = Response(raw, True)
    tool_call = ToolCall.from_response(response, tools=[])
    assert tool_call is None


def test_no_parsing_for_wrong_tool():
    raw = "def is_prime(n):\\n   return True"
    response = Response(raw, True)
    tool_call = ToolCall.from_response(response, tools=[GetGithubReadme])
    assert tool_call is None


def test_parsing_of_invalid_format_raises():
    raw = '{"name": "get_github_readme", "parameters": {"whatever": "pharia-kernel"}}'
    response = Response(raw, True)
    with pytest.raises(ValidationError):
        ToolCall.from_response(response, tools=[GetGithubReadme])
