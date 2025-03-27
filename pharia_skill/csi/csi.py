from typing import Protocol

from .chunking import Chunk, ChunkParams, ChunkRequest
from .document_index import (
    Document,
    DocumentPath,
    IndexPath,
    JsonSerializable,
    SearchFilter,
    SearchRequest,
    SearchResult,
)
from .inference import (
    ChatParams,
    ChatRequest,
    ChatResponse,
    ChatStreamResponse,
    Completion,
    CompletionParams,
    CompletionRequest,
    CompletionStreamResponse,
    ExplanationRequest,
    Granularity,
    Message,
    TextScore,
)
from .language import Language, SelectLanguageRequest


class Csi(Protocol):
    """The Cognitive System Interface (CSI) is a protocol that allows skills to interact with the Pharia Kernel."""

    def _completion_stream(
        self, model: str, prompt: str, params: CompletionParams
    ) -> CompletionStreamResponse:
        """Streams completions given a prompt.

        Parameters:
            model (str, required): Name of model to use.
            prompt (str, required): The text to be completed.
            params (CompletionParams, required): Parameters for the requested completion.
        """
        ...

    def _chat_stream(
        self, model: str, messages: list[Message], params: ChatParams
    ) -> ChatStreamResponse:
        """Streams chat with a model, where the first item is the role.

        Parameters:
            model (str, required):
                Name of model to use.

            messages (list[Message], required):
                List of messages, alternating between messages from user and assistant.

            params (ChatParams, required):
                Parameters used for the chat.
        """
        ...

    def complete(self, model: str, prompt: str, params: CompletionParams) -> Completion:
        """Generates completions given a prompt.

        Parameters:
            model (str, required): Name of model to use.
            prompt (str, required): The text to be completed.
            params (CompletionParams, required): Parameters for the requested completion.

        Examples::

            prompt = f\"\"\"<|begin_of_text|><|start_header_id|>system<|end_header_id|>

            You are a poet who strictly speaks in haikus.<|eot_id|><|start_header_id|>user<|end_header_id|>

            {input.root}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\"\"\"
            params = CompletionParams(max_tokens=64)
            completion = csi.complete("llama-3.1-8b-instruct", prompt, params)
        """
        request = CompletionRequest(model, prompt, params)
        return self.complete_concurrent([request])[0]

    def complete_concurrent(
        self, requests: list[CompletionRequest]
    ) -> list[Completion]:
        """Generate completions concurrently.

        Parameters:
            requests (list[CompletionRequest], required): List of completion requests.
        """
        ...

    def chunk(self, text: str, params: ChunkParams) -> list[Chunk]:
        """Chunks a text into chunks according to params.

        Parameters:
            text (str, required): Text to be chunked.
            params (ChunkParams, required): Parameter used for chunking, model and maximal number of tokens.

        Examples::

            text = "A very very very long text that can be chunked."
            params = ChunkParams("llama-3.1-8b-instruct", max_tokens=5)
            result = csi.chunk(text, params)
            assert len(result) == 3
        """
        request = ChunkRequest(text, params)
        return self.chunk_concurrent([request])[0]

    def chunk_concurrent(self, requests: list[ChunkRequest]) -> list[list[Chunk]]:
        """Chunk a text into chunks concurrently.

        Parameters:
            requests (list[ChunkRequest], required): List of chunk requests.
        """
        ...

    def chat(
        self, model: str, messages: list[Message], params: ChatParams
    ) -> ChatResponse:
        """Chat with a model.

        Parameters:
            model (str, required):
                Name of model to use.

            messages (list[Message], required):
                List of messages, alternating between messages from user and assistant.

            params (ChatParams, required):
                Parameters used for the chat.

        Examples::

            input = "oat milk"
            msg = Message.user(f\"\"\"You are a poet who strictly speaks in haikus.

            {input}\"\"\")
            model = "llama-3.1-8b-instruct"
            chat_response = csi.chat(model, [msg], ChatParams(max_tokens=64))
        """
        request = ChatRequest(model, messages, params)
        return self.chat_concurrent([request])[0]

    def chat_concurrent(self, requests: list[ChatRequest]) -> list[ChatResponse]:
        """Chat with a model concurrently.

        Parameters:
            requests (list[ChatRequest], required): List of chat requests.
        """
        ...

    def explain(
        self,
        prompt: str,
        target: str,
        model: str,
        granularity: Granularity = Granularity.AUTO,
    ) -> list[TextScore]:
        request = ExplanationRequest(prompt, target, model, granularity)
        return self.explain_concurrent([request])[0]

    def explain_concurrent(
        self, requests: list[ExplanationRequest]
    ) -> list[list[TextScore]]: ...

    def select_language(self, text: str, languages: list[Language]) -> Language | None:
        """Select the detected language for the provided input based on the list of possible languages.

        If no language matches, None is returned.

        Parameters:
            text (str, required): Text input.
            languages (list[Language], required): All languages that should be considered during detection.

        Examples::

            text = "Ich spreche Deutsch nur ein bisschen."
            languages = [Language.English, Language.German]
            result = csi.select_language(text, languages)
        """
        request = SelectLanguageRequest(text, languages)
        return self.select_language_concurrent([request])[0]

    def select_language_concurrent(
        self, requests: list[SelectLanguageRequest]
    ) -> list[Language | None]:
        """Detect the language for multiple texts concurrently.

        Parameters:
            requests (list[SelectLanguageRequest], required): List of select language requests.
        """
        ...

    def search(
        self,
        index_path: IndexPath,
        query: str,
        max_results: int = 1,
        min_score: float | None = None,
        filters: list[SearchFilter] | None = None,
    ) -> list[SearchResult]:
        """Search an existing Index in the Document Index.

        Parameters:
            index_path (IndexPath, required): Index path in the Document Index to access.
            query (str, required): Text to be search for.
            max_results (int, required): Maximal number of results.
            min_score (float, optional, Default NoneNone): Minimal score for result to be included.

        Examples::

            index_path = IndexPath("f13", "wikipedia-de", "luminous-base-asymmetric-64")
            query = "What is the population of Heidelberg?"
            result = csi.search(index_path, query)
            r0 = result[0]
            "Heidelberg" in r0.content, "Heidelberg" in r0.document_path.name # True, True
        """
        request = SearchRequest(
            index_path, query, max_results, min_score, filters or []
        )
        return self.search_concurrent([request])[0]

    def search_concurrent(
        self, requests: list[SearchRequest]
    ) -> list[list[SearchResult]]: ...

    """Execute multiple search requests against the Document Index."""

    def document(self, document_path: DocumentPath) -> Document:
        """Fetch a document from the Document Index.

        Parameters:
            document_path (DocumentPath, required): The document path to get the document from.

        Examples::

            document_path = DocumentPath("f13", "wikipedia-de", "Heidelberg")
            document = csi.document(document_path)
            assert document.path == document_path
        """
        return self.documents([document_path])[0]

    def documents(self, document_paths: list[DocumentPath]) -> list[Document]:
        """Fetch multiple documents from the Document Index.

        Parameters:
            document_paths (list[DocumentPath], required): The document paths to get the documents from.
        """
        ...

    def document_metadata(self, document_path: DocumentPath) -> JsonSerializable:
        """Return the metadata of a document in the Document Index.

        Parameters:
            document_path (DocumentPath, required): The document path to get metadata from.
        """
        return self.documents_metadata([document_path])[0]

    def documents_metadata(
        self, document_paths: list[DocumentPath]
    ) -> list[JsonSerializable]:
        """Return the metadata of multiple documents in the Document Index.

        Parameters:
            document_paths (list[DocumentPath], required): The document paths to get metadata from.
        """
        ...
