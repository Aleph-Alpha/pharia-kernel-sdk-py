import inspect
import traceback
from typing import Callable, Type, TypeVar

from pydantic import BaseModel

from pharia_skill import Csi
from pharia_skill.bindings import exports
from pharia_skill.bindings.imports import streaming_output as wit
from pharia_skill.bindings.types import Err
from pharia_skill.csi.streaming_output import Response
from pharia_skill.wit_csi.csi import WitCsi
from pharia_skill.wit_csi.streaming_output import WitResponse

UserInput = TypeVar("UserInput", bound=BaseModel)


def message_stream(
    func: Callable[[Csi, Response, UserInput], None],
) -> Callable[[Csi, Response, UserInput], None]:
    """Decorate a function to write messages to the output stream."""

    from pharia_skill.bindings.exports.message_stream import (
        Error_Internal,
        Error_InvalidInput,
    )

    signature = list(inspect.signature(func).parameters.values())
    assert len(signature) == 3, (
        "Message Stream Skills must have exactly three arguments."
    )

    input_model: Type[UserInput] = signature[2].annotation
    assert issubclass(input_model, BaseModel), (
        "The third argument must be a Pydantic model"
    )

    assert func.__annotations__.get("return") is None, (
        "The function must not return anything"
    )

    # We don't require the schema of the end payload in the function definition.
    # The only use case for this would be to know the metadata of the end payload.
    # Since we don't do metadata for streaming skills at the moment, it is not needed.

    class MessageStream(exports.MessageStream):
        def run(self, input: bytes, output: wit.StreamOutput) -> None:
            try:
                validated = input_model.model_validate_json(input)
            except Exception:
                raise Err(Error_InvalidInput(traceback.format_exc()))
            try:
                with WitResponse(output) as response:
                    func(WitCsi(), response, validated)
            except Exception:
                raise Err(Error_Internal(traceback.format_exc()))

    assert "MessageStream" not in func.__globals__, (
        "`@message_stream` can only be used once."
    )

    func.__globals__["MessageStream"] = MessageStream
    return func
