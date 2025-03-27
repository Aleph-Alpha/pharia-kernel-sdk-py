import inspect
import traceback
from dataclasses import dataclass
from types import TracebackType
from typing import Callable, Generic, Protocol, Self, Type, TypeVar

from pydantic import BaseModel

from pharia_skill import Csi
from pharia_skill.bindings import exports
from pharia_skill.bindings.imports import streaming_output as wit
from pharia_skill.bindings.types import Err
from pharia_skill.wit_csi.csi import WitCsi

UserInput = TypeVar("UserInput", bound=BaseModel)
Payload = TypeVar("Payload", bound=BaseModel)


@dataclass
class MessageBegin:
    role: str | None


@dataclass
class MessageAppend:
    text: str


@dataclass
class MessageEnd(Generic[Payload]):
    payload: Payload | None


MessageItem = MessageBegin | MessageAppend | MessageEnd[Payload]


def message_item_to_wit(item: MessageItem[Payload]) -> wit.MessageItem:
    match item:
        case MessageBegin():
            attributes = wit.BeginAttributes(role=item.role)
            return wit.MessageItem_MessageBegin(value=attributes)
        case MessageAppend():
            return wit.MessageItem_MessageAppend(value=item.text)
        case MessageEnd():
            data = item.payload.model_dump_json().encode() if item.payload else None
            return wit.MessageItem_MessageEnd(value=data)


class Response(Protocol):
    """Write messages to the output stream."""

    def write(self, item: MessageItem[Payload]) -> None: ...


class WitResponse(Response):
    def __init__(self, output: wit.StreamOutput):
        self.inner = output

    def __enter__(self) -> Self:
        self.inner.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        return self.inner.__exit__(exc_type, exc_value, traceback)

    def write(self, item: MessageItem[Payload]) -> None:
        message_item = message_item_to_wit(item)
        self.inner.write(message_item)


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

    # TODO: validate the message end_payload

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

    func.__globals__["MessageStream"] = MessageStream
    return func
