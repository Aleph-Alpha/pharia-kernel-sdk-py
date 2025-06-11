from pharia_skill.csi.tool import InvokeRequest
from pharia_skill.testing.dev.tool import (
    InvokeRequestListSerializer,
    Text,
    ToolOutputDeserializer,
    ToolOutputListDeserializer,
)
from tests.testing.dev.conftest import dumps


def test_serialize_invoke_request():
    requests = [InvokeRequest("add", {"a": 1, "b": 2})]

    serialized = InvokeRequestListSerializer(requests).model_dump_json()

    assert serialized == dumps([{"tool_name": "add", "arguments": {"a": 1, "b": 2}}])


def test_deserialize_tool_output():
    # Given a serialized completion response
    serialized = dumps(
        [[{"type": "text", "text": "3"}, {"type": "text", "text": "42"}]]
    )

    # When deserializing it
    deserialized = ToolOutputListDeserializer.model_validate_json(serialized)
    output = deserialized.root[0]

    # Then the completion is loaded recursively
    assert output == [
        ToolOutputDeserializer(root=Text(type="text", text="3")),
        ToolOutputDeserializer(root=Text(type="text", text="42")),
    ]
