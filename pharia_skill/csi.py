"""
This module exposes the interfaces for skills to interact with the Pharia Kernel
via the Cognitive System Interface (CSI).
"""

from dataclasses import dataclass, field
from typing import Protocol

from .wit.imports import csi
from .wit.imports.csi import (
    ChatParams as WitChatParams,
)
from .wit.imports.csi import (
    ChatResponse,
    ChunkParams,
    Completion,
    CompletionRequest,
    DocumentPath,
    FinishReason,
    IndexPath,
    Language,
    Message,
    Role,
    SearchResult,
)
from .wit.imports.csi import (
    CompletionParams as WitCompletionParams,
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


@dataclass
class ChatParams(WitChatParams):
    max_tokens: int | None = None
    temperature: float | None = None
    top_p: float | None = None


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
        return csi.complete(model, prompt, params)

    def chunk(self, text: str, params: ChunkParams) -> list[str]:
        return csi.chunk(text, params)

    def chat(
        self, model: str, messages: list[Message], params: ChatParams
    ) -> ChatResponse:
        return csi.chat(model, messages, params)

    def select_language(self, text: str, languages: list[Language]) -> Language | None:
        return csi.select_language(text, languages)

    def complete_all(self, requests: list[CompletionRequest]) -> list[Completion]:
        return csi.complete_all(requests)

    def search(
        self,
        index_path: IndexPath,
        query: str,
        max_results: int,
        min_score: float | None,
    ) -> list[SearchResult]:
        return csi.search(index_path, query, max_results, min_score)
