from pydantic import BaseModel, Field

from pharia_skill.llama3.response import Response
from pharia_skill.llama3.tool import BuiltInTool, ToolCall, ToolDefinition


def test_tool_definition_with_custom_parameters():
    tool = ToolDefinition(
        name="get_github_readme",
        description="Get the readme of a GitHub repository",
        parameters={"my_param": "my_value"},
    )
    expected = {
        "type": "function",
        "function": {
            "name": "get_github_readme",
            "description": "Get the readme of a GitHub repository",
            "parameters": {
                "my_param": "my_value",
            },
        },
    }
    assert tool.as_dict() == expected


def test_tool_definition_for_function():
    class Parameters(BaseModel):
        repository: str = Field(
            description="The name of the GitHub repository to get the readme from",
        )
        registry: str = "default"

    tool = ToolDefinition(
        name="get_github_readme",
        description="Get the readme of a GitHub repository",
        parameters=Parameters,
    )
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
    assert tool.as_dict() == expected


def test_brave_search_call_is_parsed():
    # Given a response with a call to Brave Search
    raw = '<|python_tag|>brave_search.call(query="current weather in Menlo Park, California")<|eom_id|>'
    response = Response.from_raw(raw)

    # When parsing the tool call
    tool_call = ToolCall.from_response(response)

    # Then
    assert tool_call is not None
    assert tool_call.tool_name == BuiltInTool.BraveSearch
    assert tool_call.arguments == {"query": "current weather in Menlo Park, California"}


def test_wolfram_alpha_call_is_parsed():
    # Given a response with a call to Wolfram Alpha
    raw = '<|python_tag|>wolfram_alpha.call(query="solve x^3 - 4x^2 + 6x - 24 = 0")<|eom_id|>'
    response = Response.from_raw(raw)

    # When parsing the tool call
    tool_call = ToolCall.from_response(response)

    # Then
    assert tool_call is not None
    assert tool_call.tool_name == BuiltInTool.WolframAlpha
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
        tool_name=BuiltInTool.CodeInterpreter,
        arguments={"code": "def is_prime(n):\n   return True"},
    )
    assert tool_call.render() == "<|python_tag|>def is_prime(n):\n   return True"


def test_brave_search_tool_call_render():
    tool_call = ToolCall(
        tool_name=BuiltInTool.BraveSearch,
        arguments={"query": "current weather in Menlo Park, California"},
    )
    expected = '<|python_tag|>brave_search.call(query="current weather in Menlo Park, California")'
    assert tool_call.render() == expected


def test_load_tool_definition_from_dict():
    data = {
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

    tool = ToolDefinition(**data)  # type: ignore[arg-type]
    assert tool.name == "get_github_readme"
    assert tool.description == "Get the readme of a GitHub repository"
    assert tool.as_dict() == data
