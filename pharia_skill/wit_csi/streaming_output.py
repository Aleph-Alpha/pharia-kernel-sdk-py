from types import TracebackType
from typing import Self

from ..bindings.imports import streaming_output as wit
from ..csi.streaming_output import (
    MessageAppend,
    MessageBegin,
    MessageEnd,
    MessageItem,
    Payload,
    Response,
)


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
