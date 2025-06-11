import json

from ..bindings.imports import tool as wit
from ..csi.tool import InvokeRequest, ToolOutput


def invoke_request_to_wit(request: InvokeRequest) -> wit.InvokeRequest:
    return wit.InvokeRequest(
        tool_name=request.tool_name,
        arguments=[
            wit.Argument(name=name, value=json.dumps(value).encode())
            for name, value in request.arguments.items()
        ],
    )


def tool_output_from_wit(response: list[wit.Modality]) -> ToolOutput:
    return ToolOutput(contents=[modality.value for modality in response])
