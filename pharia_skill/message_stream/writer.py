from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar

from pydantic import BaseModel

from pharia_skill.csi import inference
from pharia_skill.csi.inference import ChatStreamResponse, CompletionStreamResponse

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


@dataclass
class Reasoning:
    content: str


MessageItem = MessageBegin | Reasoning | MessageAppend | MessageEnd[Payload]


class MessageWriter(Protocol, Generic[Payload]):
    """Write messages to the output stream."""

    def write(self, item: MessageItem[Payload]) -> None: ...

    def begin_message(self, role: str | None = None) -> None:
        self.write(MessageBegin(role))

    def append_to_message(self, text: str) -> None:
        """Write some text chunks to the output stream."""
        self.write(MessageAppend(text))

    def append_to_reasoning(self, text: str) -> None:
        """Write some reasoning chunks to the output stream."""
        self.write(Reasoning(text))

    def end_message(self, payload: Payload | None = None) -> None:
        self.write(MessageEnd(payload))

    def forward_response(
        self,
        response: CompletionStreamResponse | ChatStreamResponse,
        payload: Callable[..., Payload] | Payload | None = None,
    ) -> None:
        """Forward the response of a chat completion to the output stream.

        For chat requests, this forwards both the reasoning and message chunks.
        If you need more fine-grained control over what is being exposed, use
        the `append_to_message and `append_to_reasoning` methods directly.
        """
        match response:
            case CompletionStreamResponse():
                self._forward_completion(response, payload)
            case ChatStreamResponse():
                self._forward_chat(response, payload)

    def _forward_completion(
        self,
        response: CompletionStreamResponse,
        payload: Callable[..., Payload] | Payload | None = None,
    ) -> None:
        self.begin_message()
        for append in response.stream():
            self.append_to_message(append.text)
        self.end_message(payload(response) if callable(payload) else payload)

    def _forward_chat(
        self,
        response: ChatStreamResponse,
        payload: Callable[..., Payload] | Payload | None = None,
    ) -> None:
        self.begin_message(response.role)
        for append in response.stream():
            match append:
                case inference.types.Reasoning():
                    self.append_to_reasoning(append.content)
                case inference.types.MessageAppend():
                    self.append_to_message(append.content)
        self.end_message(payload(response) if callable(payload) else payload)
