from pharia_skill.csi.tool import InvokeRequest, ToolOutput
from pharia_skill.testing.dev.tool import (
    deserialize_tool_output,
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
    # Given a serialized completion response
    serialized = [[{"type": "text", "text": "3"}, {"type": "text", "text": "42"}]]

    # When deserializing it
    output = deserialize_tool_output(serialized)

    # Then the completion is loaded recursively
    assert output == [ToolOutput(contents=["3", "42"])]
