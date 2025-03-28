from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar

from pydantic import BaseModel

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


class Response(Protocol):
    """Write messages to the output stream."""

    def write(self, item: MessageItem[Payload]) -> None: ...
