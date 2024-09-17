"""
This module exposes the interfaces for skills to interact with the Pharia Kernel
via the Cognitive System Interface (CSI).
"""

from dataclasses import dataclass, field
from typing import Optional, Protocol

from .wit.imports import csi
from .wit.imports.csi import (
    ChunkParams,
    Completion,
    CompletionRequest,
    FinishReason,
    Language,
)
from .wit.imports.csi import (
    CompletionParams as WitCompletionParams,
)

__all__ = [
    "ChunkParams",
    "Completion",
    "CompletionParams",
    "CompletionRequest",
    "Csi",
    "FinishReason",
    "Language",
]


@dataclass
class CompletionParams(WitCompletionParams):
    max_tokens: int | None = None
    temperature: float | None = None
    top_k: int | None = None
    top_p: float | None = None
    stop: list[str] = field(default_factory=lambda: list())


class Csi(Protocol):
    @staticmethod
    def complete(model: str, prompt: str, params: CompletionParams) -> Completion: ...

    @staticmethod
    def chunk(text: str, params: ChunkParams) -> list[str]: ...

    @staticmethod
    def select_language(text: str, languages: list[Language]) -> Language | None: ...

    @staticmethod
    def complete_all(requests: list[CompletionRequest]) -> list[Completion]: ...


class WasiCsi(Csi):
    @staticmethod
    def complete(model: str, prompt: str, params: CompletionParams) -> Completion:
        return csi.complete(model, prompt, params)

    @staticmethod
    def chunk(text: str, params: ChunkParams) -> list[str]:
        return csi.chunk(text, params)

    @staticmethod
    def select_language(text: str, languages: list[Language]) -> Language | None:
        return csi.select_language(text, languages)

    @staticmethod
    def complete_all(requests: list[CompletionRequest]) -> list[Completion]:
        return csi.complete_all(requests)
