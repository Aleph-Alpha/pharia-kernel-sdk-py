from typing import Any, Literal, Sequence, Union

from pydantic import BaseModel, Field, RootModel
from pydantic.types import JsonValue

from pharia_skill.csi.inference import tool


class ArgumentSerializer(BaseModel):
    name: str
    value: JsonValue


class InvokeRequestSerializer(BaseModel):
    """Serialization representation of a single tool invocation.

    Must be nested inside a `InvokeRequestsSerializer` that provides the `namespace`.
    """

    name: str
    arguments: list[ArgumentSerializer]


class InvokeRequestsSerializer(BaseModel):
    namespace: str
    requests: list[InvokeRequestSerializer]


def serialize_tool_requests(
    namespace: str, requests: Sequence[tool.InvokeRequest]
) -> dict[str, Any]:
    return InvokeRequestsSerializer(
        namespace=namespace,
        requests=[
            InvokeRequestSerializer(
                name=request.name,
                arguments=[
                    ArgumentSerializer(name=name, value=value)
                    for name, value in request.arguments.items()
                ],
            )
            for request in requests
        ],
    ).model_dump()


class Text(BaseModel):
    type: Literal["text"]
    text: str


# Pylance complains about a Union of only one type.
# However, for discriminated deserialization we do require the Union.
class ToolModalityDeserializer(RootModel[Union[Text]]):  # pyright: ignore[reportInvalidTypeArguments]
    root: Union[Text] = Field(discriminator="type")  # pyright: ignore[reportInvalidTypeArguments]


ToolOutputListDeserializer = RootModel[list[list[ToolModalityDeserializer] | str]]
"""Deserialization of the tool output.

In the success case, we receive a list of modalities. In the error case a string.
"""


def deserialize_tool_output(output: Any) -> list[tool.ToolResult]:
    return [
        tool.ToolOutput(contents=[content.root.text for content in deserialized])
        if isinstance(deserialized, list)
        else tool.ToolError(message=deserialized)
        for deserialized in ToolOutputListDeserializer(root=output).root
    ]


class ToolDeserializer(BaseModel):
    name: str
    description: str
    input_schema: dict[str, JsonValue]


ToolListDeserializer = RootModel[list[ToolDeserializer]]


def deserialize_tools(output: Any) -> list[tool.Tool]:
    return [
        tool.Tool(name=t.name, description=t.description, input_schema=t.input_schema)
        for t in ToolListDeserializer(root=output).root
    ]
