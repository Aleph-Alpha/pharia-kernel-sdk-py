from pharia_skill.csi.tool import InvokeRequest, Tool, ToolError, ToolOutput
from pharia_skill.testing.dev.tool import (
    deserialize_tool_output,
    deserialize_tools,
    serialize_tool_requests,
)


def test_serialize_invoke_request():
    # Given a tool invocation
    serialized = serialize_tool_requests(
        namespace="test", requests=[InvokeRequest("add", {"a": 1, "b": 2})]
    )

    assert serialized == {
        "namespace": "test",
        "requests": [
            {
                "name": "add",
                "arguments": [{"name": "a", "value": 1}, {"name": "b", "value": 2}],
            }
        ],
    }


def test_deserialize_tool_output():
    # Given a serialized tool output
    serialized = [[{"type": "text", "text": "3"}, {"type": "text", "text": "42"}]]

    # When deserializing it
    output = deserialize_tool_output(serialized)

    # Then the tool output is loaded
    assert output == [ToolOutput(contents=["3", "42"])]


def test_deserialize_tool_error_output():
    # Given a serialized tool error output
    serialized = ["No fish caught."]

    # When deserializing it
    output = deserialize_tool_output(serialized)

    # Then the tool error is loaded
    assert output == [ToolError(message="No fish caught.")]


def test_deserialize_mixed_tool_output():
    # Given a serialized tool invocation with one success and one error
    serialized = [[{"type": "text", "text": "3"}], "No fish caught."]

    # When deserializing it
    output = deserialize_tool_output(serialized)

    # Then the tool output and error are loaded
    assert output == [ToolOutput(contents=["3"]), ToolError(message="No fish caught.")]


def test_deserialize_tools():
    # Given two serialized tools
    serialized = [
        {
            "name": "add",
            "description": "Add two numbers",
            "input_schema": {"a": {"type": "number"}, "b": {"type": "number"}},
        },
        {
            "name": "subtract",
            "description": "Subtract two numbers",
            "input_schema": {"a": {"type": "number"}, "b": {"type": "number"}},
        },
    ]

    # When deserializing them
    output = deserialize_tools(serialized)

    # Then the tools are loaded
    assert output == [
        Tool(
            name="add",
            description="Add two numbers",
            input_schema={"a": {"type": "number"}, "b": {"type": "number"}},
        ),
        Tool(
            name="subtract",
            description="Subtract two numbers",
            input_schema={"a": {"type": "number"}, "b": {"type": "number"}},
        ),
    ]
