"""
This module references bindings which can only be resolved if targeting the `message-stream-skill` world.

Having this module in the import graph when targeting the `skill` world will lead to a build error.
"""

from types import TracebackType
from typing import Self

from pharia_skill.bindings.imports import streaming_output as wit

from .writer import (
    MessageAppend,
    MessageBegin,
    MessageEnd,
    MessageItem,
    MessageWriter,
    Payload,
)


def message_item_to_wit(item: MessageItem[Payload]) -> wit.MessageItem:
    match item:
        case MessageBegin(role):
            attributes = wit.BeginAttributes(role=role)
            return wit.MessageItem_MessageBegin(value=attributes)
        case MessageAppend(text):
            return wit.MessageItem_MessageAppend(value=text)
        case MessageEnd(payload):
            data = payload.model_dump_json().encode() if payload is not None else None
            return wit.MessageItem_MessageEnd(value=data)


class WitMessageWriter(MessageWriter[Payload]):
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
