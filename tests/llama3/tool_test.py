from pydantic import BaseModel, Field

from pharia_skill.llama3.tool import BuiltInTool, ToolCall, ToolDefinition


def test_code_interpreter_tool_call_render():
    tool_call = ToolCall(
        tool_name=BuiltInTool.CodeInterpreter,
        arguments={"code": "def is_prime(n):\n   return True"},
    )
    assert tool_call.render() == "def is_prime(n):\n   return True"


def test_brave_search_tool_call_render():
    tool_call = ToolCall(
        tool_name=BuiltInTool.BraveSearch,
        arguments={"query": "current weather in Menlo Park, California"},
    )
    expected = 'brave_search.call(query="current weather in Menlo Park, California")'
    assert tool_call.render() == expected


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
