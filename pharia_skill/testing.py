"""
StubCsi can be used for testing without a backing Pharia Kernel instance.
"""

from dataclasses import asdict

from .csi import (
    ChunkParams,
    Completion,
    CompletionParams,
    CompletionRequest,
    Csi,
    FinishReason,
    Language,
)


class StubCsi(Csi):
    @staticmethod
    def complete(model: str, prompt: str, params: CompletionParams) -> Completion:
        return Completion(
            text=prompt,
            finish_reason=FinishReason.STOP,
        )

    @staticmethod
    def chunk(text: str, params: ChunkParams) -> list[str]:
        return [text]

    @staticmethod
    def select_language(text: str, languages: list[Language]) -> Language | None:
        return languages[0] if languages else None

    @staticmethod
    def complete_all(requests: list[CompletionRequest]) -> list[Completion]:
        return [StubCsi.complete(**asdict(request)) for request in requests]
