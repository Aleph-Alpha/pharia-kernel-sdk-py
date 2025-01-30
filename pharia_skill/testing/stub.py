"""
StubCsi can be used for testing without a backing Pharia Kernel instance.
"""

from dataclasses import asdict

from pharia_skill import (
    ChatParams,
    ChatResponse,
    ChunkParams,
    Completion,
    CompletionParams,
    CompletionRequest,
    Csi,
    Document,
    DocumentPath,
    FinishReason,
    IndexPath,
    JsonSerializable,
    Language,
    Message,
    SearchResult,
    Text,
)


class StubCsi(Csi):
    """
    The `StubCsi` can be used to mock out the CSI for testing purposes.

    You can use this class directly, or inherit from it and load it up with your own expectations.
    Suppose you want to test a Skill that uses the `chat` method, and want to mock out the response from the LLM
    to run your tests faster:

    Example::

        from pharia_skill import Csi, skill

        @skill
        def run(csi: Csi, input: Input) -> Output:
            system = Message.system("You are a poet who strictly speaks in haikus.")
            user = Message.user(input.topic)
            params = ChatParams(max_tokens=64)
            response = csi.chat("llama-3.1-8b-instruct", [system, user], params)
            return Output(haiku=response.message.content.strip())

        class CustomMockCsi(StubCsi):
            def chat(self, model: str, messages: list[Message], params: ChatParams) -> ChatResponse:
                message = Message.assistant("Whispers in the dark\nEchoes of a fleeting dream\nMeaning lost in space")
                return ChatResponse(message=message, finish_reason=FinishReason.STOP)

        def test_run():
            csi = CustomMockCsi()
            result = run(csi, Input(topic="The meaning of life"))
            assert result.haiku == "Whispers in the dark\nEchoes of a fleeting dream\nMeaning lost in space"
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
        return [self.complete(**asdict(request)) for request in requests]

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

    def documents(self, document_paths: list[DocumentPath]) -> list[Document]:
        return [
            Document(
                path=document_path,
                contents=[Text("dummy-content")],
                metadata=None,
            )
            for document_path in document_paths
        ]

    def document_metadata(self, document_path: DocumentPath) -> JsonSerializable:
        return {}
