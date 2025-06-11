from typing import Any, Literal, Sequence, Union

from pydantic import BaseModel, Field, RootModel

from pharia_skill import ToolOutput
from pharia_skill.csi.tool import InvokeRequest


class Text(BaseModel):
    type: Literal["text"]
    text: str


class ToolOutputDeserializer(RootModel[Union[Text]]):
    root: Union[Text] = Field(discriminator="type")


InvokeRequestListSerializer = RootModel[Sequence[InvokeRequest]]

ToolOutputListDeserializer = RootModel[list[list[ToolOutputDeserializer]]]


def validate_tool_output(output: Any) -> list[ToolOutput]:
    return [
        ToolOutput(contents=[content.root.text for content in deserialized])
        for deserialized in ToolOutputListDeserializer(root=output).root
    ]
