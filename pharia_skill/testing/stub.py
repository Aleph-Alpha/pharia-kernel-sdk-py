"""
StubCsi can be used for testing without a backing Pharia Kernel instance.
"""

from dataclasses import asdict

from ..csi import (
    ChunkParams,
    Completion,
    CompletionParams,
    CompletionRequest,
    Csi,
    FinishReason,
    Language,
)


class StubCsi(Csi):
    def complete(self, model: str, prompt: str, params: CompletionParams) -> Completion:
        return Completion(
            text=prompt,
            finish_reason=FinishReason.STOP,
        )

    def chunk(self, text: str, params: ChunkParams) -> list[str]:
        return [text]

    def select_language(self, text: str, languages: list[Language]) -> Language | None:
        return languages[0] if languages else None

    def complete_all(self, requests: list[CompletionRequest]) -> list[Completion]:
        return [self.complete(**asdict(request)) for request in requests]
