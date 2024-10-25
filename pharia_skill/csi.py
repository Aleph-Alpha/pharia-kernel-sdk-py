"""
This module exposes the interfaces for skills to interact with the Pharia Kernel
via the Cognitive System Interface (CSI).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol

from .wit.imports import csi
from .wit.imports.csi import (
    ChatParams as WitChatParams,
)
from .wit.imports.csi import (
    ChatResponse as WitChatResponse,
)
from .wit.imports.csi import (
    ChunkParams,
    CompletionRequest,
    DocumentPath,
    IndexPath,
    Language,
    SearchResult,
)
from .wit.imports.csi import (
    Completion as WitCompletion,
)
from .wit.imports.csi import (
    CompletionParams as WitCompletionParams,
)
from .wit.imports.csi import (
    FinishReason as WitFinishReason,
)
from .wit.imports.csi import (
    Message as WitMessage,
)
from .wit.imports.csi import (
    Role as WitRole,
)

__all__ = [
    "ChatParams",
    "ChatResponse",
    "Message",
    "Role",
    "ChunkParams",
    "Completion",
    "CompletionParams",
    "CompletionRequest",
    "Csi",
    "FinishReason",
    "Language",
    "SearchResult",
    "DocumentPath",
    "IndexPath",
]


@dataclass
class CompletionParams(WitCompletionParams):
    max_tokens: int | None = None
    temperature: float | None = None
    top_k: int | None = None
    top_p: float | None = None
    stop: list[str] = field(default_factory=lambda: list())


class FinishReason(str, Enum):
    STOP = "stop"
    LENGTH = "length"
    CONTENT_FILTER = "content_filter"

    @classmethod
    def from_wit(cls, reason: WitFinishReason) -> "FinishReason":
        match reason:
            case WitFinishReason.STOP:
                return FinishReason.STOP
            case WitFinishReason.LENGTH:
                return FinishReason.LENGTH
            case WitFinishReason.CONTENT_FILTER:
                return FinishReason.CONTENT_FILTER


@dataclass
class Completion:
    text: str
    finish_reason: FinishReason

    @classmethod
    def from_wit(cls, completion: WitCompletion) -> "Completion":
        return cls(
            text=completion.text,
            finish_reason=FinishReason.from_wit(completion.finish_reason),
        )


@dataclass
class ChatParams(WitChatParams):
    max_tokens: int | None = None
    temperature: float | None = None
    top_p: float | None = None


class Role(str, Enum):
    User = "User"
    Assistant = "Assistant"
    System = "System"

    @property
    def wit(self) -> WitRole:
        match self:
            case Role.User:
                return WitRole.USER
            case Role.Assistant:
                return WitRole.ASSISTANT
            case Role.System:
                return WitRole.SYSTEM

    @classmethod
    def from_wit(cls, role: WitRole) -> "Role":
        match role:
            case WitRole.USER:
                return Role.User
            case WitRole.ASSISTANT:
                return Role.Assistant
            case WitRole.SYSTEM:
                return Role.System


@dataclass
class Message:
    role: Role
    content: str

    @property
    def wit(self) -> WitMessage:
        return WitMessage(role=self.role.wit, content=self.content)

    @classmethod
    def from_wit(cls, msg: WitMessage) -> "Message":
        return cls(role=Role.from_wit(msg.role), content=msg.content)

    @classmethod
    def user(cls, content: str) -> "Message":
        return cls(role=Role.User, content=content)

    @classmethod
    def assistant(cls, content: str) -> "Message":
        return cls(role=Role.Assistant, content=content)

    @classmethod
    def system(cls, content: str) -> "Message":
        return cls(role=Role.System, content=content)


@dataclass
class ChatResponse:
    """
    The result of a chat response, including the message generated as well as
    why the model finished completing.
    """

    message: Message
    finish_reason: FinishReason

    @classmethod
    def from_wit(cls, res: WitChatResponse) -> "ChatResponse":
        return cls(
            message=Message.from_wit(res.message),
            finish_reason=FinishReason.from_wit(res.finish_reason),
        )

    @classmethod
    def from_dict(cls, body: dict) -> "ChatResponse":
        return cls(
            message=Message(**body["message"]),
            finish_reason=FinishReason(body["finish_reason"]),
        )


class Csi(Protocol):
    def complete(
        self, model: str, prompt: str, params: CompletionParams
    ) -> Completion: ...

    def chunk(self, text: str, params: ChunkParams) -> list[str]: ...

    def chat(
        self, model: str, messages: list[Message], params: ChatParams
    ) -> ChatResponse: ...

    def select_language(
        self, text: str, languages: list[Language]
    ) -> Language | None: ...

    def complete_all(self, requests: list[CompletionRequest]) -> list[Completion]: ...

    def search(
        self,
        index_path: IndexPath,
        query: str,
        max_results: int,
        min_score: float | None,
    ) -> list[SearchResult]: ...


class WasiCsi(Csi):
    def complete(self, model: str, prompt: str, params: CompletionParams) -> Completion:
        completion = csi.complete(model, prompt, params)
        return Completion.from_wit(completion)

    def chunk(self, text: str, params: ChunkParams) -> list[str]:
        return csi.chunk(text, params)

    def chat(
        self, model: str, messages: list[Message], params: ChatParams
    ) -> ChatResponse:
        response = csi.chat(model, [m.wit for m in messages], params)
        return ChatResponse.from_wit(response)

    def select_language(self, text: str, languages: list[Language]) -> Language | None:
        return csi.select_language(text, languages)

    def complete_all(self, requests: list[CompletionRequest]) -> list[Completion]:
        completions = csi.complete_all(requests)
        return [Completion.from_wit(completion) for completion in completions]

    def search(
        self,
        index_path: IndexPath,
        query: str,
        max_results: int,
        min_score: float | None,
    ) -> list[SearchResult]:
        return csi.search(index_path, query, max_results, min_score)
