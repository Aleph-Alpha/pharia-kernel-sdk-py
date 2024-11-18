"""
StubCsi can be used for testing without a backing Pharia Kernel instance.
"""

from pharia_skill import (
    ChatParams,
    ChatResponse,
    ChunkParams,
    Completion,
    CompletionParams,
    CompletionRequest,
    Csi,
    DocumentPath,
    FinishReason,
    IndexPath,
    Language,
    Message,
    SearchResult,
)


class StubCsi(Csi):
    """
    StubCsi can be used for checking whether Skill code compiles.

    This implementation of Cognitive System Interface (CSI) is provides a stub.
    This can also be used as a base class for mock implementation.
    """

    def complete(self, model: str, prompt: str, params: CompletionParams) -> Completion:
        return Completion(
            text=prompt,
            finish_reason=FinishReason.STOP,
        )

    def chunk(self, text: str, params: ChunkParams) -> list[str]:
        return [text]

    def chat(
        self, model: str, messages: list[Message], params: ChatParams
    ) -> ChatResponse:
        return ChatResponse(
            message=Message.assistant(messages[-1].content),
            finish_reason=FinishReason.STOP,
        )

    def select_language(self, text: str, languages: list[Language]) -> Language | None:
        return languages[0] if languages else None

    def complete_all(self, requests: list[CompletionRequest]) -> list[Completion]:
        return [self.complete(**request.model_dump()) for request in requests]

    def search(
        self,
        index_path: IndexPath,
        query: str,
        max_results: int = 1,
        min_score: float | None = None,
    ) -> list[SearchResult]:
        return [
            SearchResult(
                document_path=DocumentPath(
                    namespace="dummy-namespace",
                    collection="dummy-collection",
                    name="dummy-name",
                ),
                content="dummy-content",
                score=1.0,
            )
        ]
