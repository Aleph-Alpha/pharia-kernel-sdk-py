from dataclasses import dataclass
from types import TracebackType
from typing import Callable, Protocol, Self, TypeVar

from pydantic import BaseModel

from pharia_skill import ChatParams, Csi, Message
from pharia_skill.bindings import exports
from pharia_skill.bindings.imports import streaming_output as wit
from pharia_skill.wit_csi import WitCsi

UserInput = TypeVar("UserInput", bound=BaseModel)
Payload = TypeVar("Payload", bound=BaseModel)


@dataclass
class MessageBegin:
    role: str | None


@dataclass
class MessageAppend:
    text: str


@dataclass
class MessageEnd[Payload]:
    payload: Payload | None


MessageItem = MessageBegin | MessageAppend | MessageEnd[Payload]


def message_item_to_wit(item: MessageItem) -> wit.MessageItem:
    match item:
        case MessageBegin():
            attributes = wit.BeginAttributes(role=item.role)
            return wit.MessageItem_MessageBegin(value=attributes)
        case MessageAppend():
            return wit.MessageItem_MessageAppend(value=item.text)
        case MessageEnd():
            return wit.MessageItem_MessageEnd(value=item.payload)


class Output(Protocol):
    """Write messages to the output stream."""

    def write(self, item: MessageItem) -> None: ...


class WitOutput(Output):
    def __init__(self):
        self.inner = wit.StreamOutput()

    def __enter__(self) -> Self:
        self.inner.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        self.inner.__exit__(exc_type, exc_value, traceback)

    def write(self, item: MessageItem) -> None:
        message_item = message_item_to_wit(item)
        self.inner.write(message_item)


def message_stream(
    func: Callable[[Csi, Output, UserInput], None],
) -> Callable[[Csi, Output, UserInput], None]:
    """Decorate a function to write messages to the output stream."""

    # class MessageStreamHandler(exports.MessageStreamHandler):
    #     def run(self, input: bytes) -> bytes:
    #         with WitOutput() as output:
    #             return func(WitCsi(), output, input)

    return func


class Input(BaseModel):
    topic: str


@message_stream
def haiku_stream(csi: Csi, output: Output, input: Input) -> None:
    response = csi.chat_stream(
        model="llama-3.1-8b-instruct",
        messages=[Message.user(input.topic)],
        params=ChatParams(),
    )
    output.write(MessageBegin(response.role))
    for event in response.stream():
        output.write(MessageAppend(event.content))
    output.write(MessageEnd(response.finish_reason))
