import inspect
import traceback
from typing import Callable, Type, TypeVar

from pydantic import BaseModel

from pharia_skill import Csi
from pharia_skill.message_stream.response import Payload, Response

UserInput = TypeVar("UserInput", bound=BaseModel)


def message_stream(
    func: Callable[[Csi, Response[Payload], UserInput], None],
) -> Callable[[Csi, Response[Payload], UserInput], None]:
    """Turn a function with a specific signature into a (streaming) skill that can be deployed on Pharia Kernel.

    By using the response object, a Skill decorated with `@message_stream` can return intermediate results
    that are streamed to the caller.

    The decorated function must be typed. It must have exactly three arguments. The first argument
    must be of type `Csi`. The second argument must be a `Response` object. The third argument
    must be a Pydantic model. The function must not return anything.

    Example::

        from pharia_skill import Csi, ChatParams, Message, message_stream, Response, MessageBegin, MessageAppend, MessageEnd
        from pydantic import BaseModel
        from pharia_skill.csi.inference import FinishReason

        class Input(BaseModel):
            topic: str

        class SkillOutput(BaseModel):
            finish_reason: FinishReason

        @message_stream
        def haiku_stream(csi: Csi, response: Response[SkillOutput], input: Input) -> None:
            with csi.chat_stream(
                model="llama-3.1-8b-instruct",
                messages=[
                    Message.system("You are a poet who strictly speaks in haikus."),
                    Message.user(input.topic),
                ],
                params=ChatParams(),
            ) as chat_response:
                response.write(MessageBegin(role=chat_response.role))
                response.write(MessageAppend(chat_response.message.content))
                for event in chat_response.stream():
                    response.write(MessageAppend(event.content))
                response.write(MessageEnd(payload=SkillOutput(finish_reason=chat_response.finish_reason())))
    """
    # The import is inside the decorator to ensure the imports only run when the decorator is interpreted.
    # This is because we can only import them when targeting the `message-stream-skill` world.
    # If we target the `skill` world with a component and have the imports for the `message-stream-skill` world
    # in this module at the top-level, we will get a build error in case this module is in the module graph.
    from pharia_skill.bindings import exports
    from pharia_skill.bindings.exports.message_stream import (
        Error_Internal,
        Error_InvalidInput,
    )
    from pharia_skill.bindings.imports import streaming_output as wit
    from pharia_skill.bindings.types import Err
    from pharia_skill.message_stream.wit_response import WitResponse
    from pharia_skill.wit_csi.csi import WitCsi

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
                with WitResponse[Payload](output) as response:
                    func(WitCsi(), response, validated)
            except Exception:
                raise Err(Error_Internal(traceback.format_exc()))

    assert "MessageStream" not in func.__globals__, (
        "`@message_stream` can only be used once."
    )

    func.__globals__["MessageStream"] = MessageStream
    return func
