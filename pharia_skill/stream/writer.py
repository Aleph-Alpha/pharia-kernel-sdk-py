from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar

from pydantic import BaseModel

Payload = TypeVar("Payload", bound=BaseModel | None)


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


class MessageWriter(Protocol, Generic[Payload]):
    """Write messages to the output stream."""

    def write(self, item: MessageItem[Payload]) -> None: ...

    def begin_message(self, role: str | None = None) -> None:
        self.write(MessageBegin(role))

    def append_to_message(self, text: str) -> None:
        self.write(MessageAppend(text))

    def end_message(self, payload: Payload | None = None) -> None:
        self.write(MessageEnd(payload))
