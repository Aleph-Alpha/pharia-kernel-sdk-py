"""
StubCsi can be used for testing without a backing Pharia Kernel instance.
"""

from collections.abc import Generator

from pharia_skill import (
    ChatParams,
    ChatRequest,
    ChatResponse,
    Chunk,
    ChunkRequest,
    Completion,
    CompletionParams,
    CompletionRequest,
    Csi,
    Cursor,
    Document,
    DocumentPath,
    ExplanationRequest,
    FinishReason,
    JsonSerializable,
    Language,
    Message,
    SearchRequest,
    SearchResult,
    SelectLanguageRequest,
    Text,
    TextScore,
    TokenUsage,
)
from pharia_skill.csi.inference import (
    ChatEvent,
    ChatStreamResponse,
    CompletionAppend,
    CompletionEvent,
    CompletionStreamResponse,
    MessageAppend,
    MessageBegin,
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

    def completion_stream(
        self, model: str, prompt: str, params: CompletionParams
    ) -> CompletionStreamResponse:
        class StubCompletionStreamResponse(CompletionStreamResponse):
            def __init__(self, stream: Generator[CompletionEvent, None, None]):
                self._stream = stream

            def next(self) -> CompletionEvent | None:
                return next(self._stream, None)

        def generator() -> Generator[CompletionEvent, None, None]:
            for char in prompt:
                yield CompletionAppend(char, [])
            yield FinishReason.STOP
            yield TokenUsage(len(prompt), len(prompt))

        return StubCompletionStreamResponse(generator())

    def chat_stream(
        self, model: str, messages: list[Message], params: ChatParams
    ) -> ChatStreamResponse:
        class StubChatStreamResponse(ChatStreamResponse):
            def __init__(self, stream: Generator[ChatEvent, None, None]):
                self._stream = stream
                super().__init__()

            def next(self) -> ChatEvent | None:
                return next(self._stream, None)

        def generator() -> Generator[ChatEvent, None, None]:
            total_usage = 0
            yield MessageBegin(messages[0].role)
            for message in messages:
                content = message.content
                total_usage += len(content)
                yield MessageAppend(content, [])
            yield FinishReason.STOP
            yield TokenUsage(total_usage, total_usage)

        return StubChatStreamResponse(generator())

    def complete_concurrent(
        self, requests: list[CompletionRequest]
    ) -> list[Completion]:
        return [
            Completion(
                text=request.prompt,
                finish_reason=FinishReason.STOP,
                logprobs=[],
                usage=TokenUsage(
                    prompt=len(request.prompt), completion=len(request.prompt)
                ),
            )
            for request in requests
        ]

    def chunk_concurrent(self, requests: list[ChunkRequest]) -> list[list[Chunk]]:
        return [[Chunk(text=request.text, offset=0)] for request in requests]

    def chat_concurrent(self, requests: list[ChatRequest]) -> list[ChatResponse]:
        return [
            ChatResponse(
                message=Message.assistant(request.messages[-1].content),
                finish_reason=FinishReason.STOP,
                logprobs=[],
                usage=TokenUsage(
                    prompt=len(request.messages[-1].content),
                    completion=len(request.messages[-1].content),
                ),
            )
            for request in requests
        ]

    def explain_concurrent(
        self, requests: list[ExplanationRequest]
    ) -> list[list[TextScore]]:
        return [[] for _ in requests]

    def select_language_concurrent(
        self, requests: list[SelectLanguageRequest]
    ) -> list[Language | None]:
        return [
            request.languages[0] if request.languages else None for request in requests
        ]

    def search_concurrent(
        self, requests: list[SearchRequest]
    ) -> list[list[SearchResult]]:
        return [
            [
                SearchResult(
                    document_path=DocumentPath(
                        namespace="dummy-namespace",
                        collection="dummy-collection",
                        name="dummy-name",
                    ),
                    content="dummy-content",
                    score=1.0,
                    start=Cursor(item=0, position=0),
                    end=Cursor(item=0, position=0),
                )
            ]
            for _ in requests
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

    def documents_metadata(
        self, document_paths: list[DocumentPath]
    ) -> list[JsonSerializable]:
        return [{} for _ in document_paths]
