from typing import Protocol

from .wit.imports import csi
from .wit.imports.csi import (
    ChunkParams,
    Completion,
    CompletionParams,
    CompletionRequest,
    Language,
)


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
