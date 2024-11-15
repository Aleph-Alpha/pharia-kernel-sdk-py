"""
This module exposes the interfaces for skills to interact with the Pharia Kernel
via the Cognitive System Interface (CSI).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol

__all__ = [
    "ChatParams",
    "ChatResponse",
    "ChunkParams",
    "Completion",
    "CompletionParams",
    "CompletionRequest",
    "Csi",
    "DocumentPath",
    "FinishReason",
    "IndexPath",
    "Language",
    "Message",
    "Role",
    "SearchResult",
]


@dataclass
class CompletionParams:
    """Completion request parameters.

    Attributes:
        max-tokens (int, optional, default None): The maximum tokens that should be inferred.
            Note, the backing implementation may return less tokens due to other stop reasons.
        temperature (float, optional, default None): The randomness with which the next token is selected.
        top-k (int, optional, default None): The number of possible next tokens the model will choose from.
        top-p (float, optional, default None): The probability total of next tokens the model will choose from.
        stop (list(str), optional, default []): A list of sequences that, if encountered, the API will stop generating further tokens.
    """

    max_tokens: int | None = None
    temperature: float | None = None
    top_k: int | None = None
    top_p: float | None = None
    stop: list[str] = field(default_factory=lambda: list())


class FinishReason(str, Enum):
    """The reason the model finished generating.

    Attributes:
        STOP: The model hit a natural stopping point or a provided stop sequence.
        LENGTH: The maximum number of tokens specified in the request was reached.
        CONTENT_FILTER: Content was omitted due to a flag from content filters.
    """

    STOP = "stop"
    LENGTH = "length"
    CONTENT_FILTER = "content_filter"


@dataclass
class Completion:
    """The result of a completion, including the text generated as well as
    why the model finished completing.

    text (str, required): The text generated by the model.
    finish-reason : The reason the model finished generating.
    """

    text: str
    finish_reason: FinishReason


@dataclass
class CompletionRequest:
    """Completion request request parameters for complete_all.

    Attributes:
        model (str, required): Name of model to use.
        prompt (str, required): The text to be completed.
        params (CompletionParams, required): Parameters for the requested completion.
    """

    model: str
    prompt: str
    params: CompletionParams


@dataclass
class ChatParams:
    """Chat request parameters.

    Attributes:
        max-tokens (int, optional, default None):  The maximum tokens that should be inferred.
            Note, the backing implementation may return less tokens due to other stop reasons.
        temperature (float, optional, default None): The randomness with which the next token is selected.
        top-p (float, optional, default None): The probability total of next tokens the model will choose from.
    """

    max_tokens: int | None = None
    temperature: float | None = None
    top_p: float | None = None


class Role(str, Enum):
    """A role used for a message in a chat."""

    User = "User"
    Assistant = "Assistant"
    System = "System"


@dataclass
class Message:
    """Describes a message in a chat.

    Parameters:
        role (Role, required): The role of the message.
        content (str, required): The content of the message.
    """

    role: Role
    content: str

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
    """The result of a chat response.

    Attributes:
        message (Message): The generated message.
        finish_reason (FinishReason): Why the model finished completing.
    """

    message: Message
    finish_reason: FinishReason


@dataclass
class ChunkParams:
    """Chunking parameters.

    Attributes:
        model (str, required): The name of the model the chunk is intended to be used for. This must be a known model.
        max_tokens (int, required): The maximum number of tokens that should be returned per chunk.
    """

    model: str
    max_tokens: int


@dataclass
class DocumentPath:
    """Path identifying a document.

    A DocumentPath consists of a namespace, within the namespace a collection and within the collection a document has a name.

    Attributes:
        namespace (str): The namespace.
        collection (str): The collection within the namespace.
        name (str): The name identifying the document in the collection.
    """

    namespace: str
    collection: str
    name: str


@dataclass
class IndexPath:
    """Which documents you want to search in, and which type of index should be used.

    Attributes:
        namespace (string): The namespace the collection belongs to.
        collection (string): The collection you want to search in.
        index (str): The search index you want to use for the collection.
    """

    namespace: str
    collection: str
    index: str


@dataclass
class SearchResult:
    """The relevant documents as result of a search request.

    Attributes:
        document_path (DocumentPath): The document_path that identifies the document.
        content (str): The contents of the retrieved document.
        score (float): The score representing the match regarding the search request.
    """

    document_path: DocumentPath
    content: str
    score: float


@dataclass
class Language(int, Enum):
    """ISO 639-3 language.

    Attributes:
        ENG (0): English.
        DEU (1): German.
    """

    ENG = 0
    DEU = 1


class Csi(Protocol):
    def complete(self, model: str, prompt: str, params: CompletionParams) -> Completion:
        """Generates completions given a prompt.

        Parameters:
            model (str, required): Name of model to use.
            prompt (str, required): The text to be completed.
            params (CompletionParams, required): Parameters for the requested completion.

        Examples:
            >>> prompt = f'''<|begin_of_text|><|start_header_id|>system<|end_header_id|>

            You are a poet who strictly speaks in haikus.<|eot_id|><|start_header_id|>user<|end_header_id|>

            {input.root}<|eot_id|><|start_header_id|>assistant<|end_header_id|>'''
            >>> params = CompletionParams(max_tokens=64)
            >>> completion = csi.complete("llama-3.1-8b-instruct", prompt, params)
        """

    def chunk(self, text: str, params: ChunkParams) -> list[str]:
        """Chunks a text into chunks according to params.

        Parameters:
            text (str, required): Text to be chunked.
            params (ChunkParams, required): Parameter used for chunking, model and maximal number of tokens.

        Examples:
            >>> text = "A very very very long text that can be chunked."
            >>> params = ChunkParams("llama-3.1-8b-instruct", max_tokens=5)
            >>> result = csi.chunk(text, params)
            >>> assert len(result) == 3
        """

    def chat(
        self, model: str, messages: list[Message], params: ChatParams
    ) -> ChatResponse:
        """Chat with a model.

        Parameters:
            model (str, required): Name of model to use.
            messages (list[Message], required): List of messages, alternating between messages from user and system.
            params (ChatParams, required): Parameters used for the chat.
        Examples:
            >>> input = "oat milk"
            >>> msg = Message.user(f"You are a poet who strictly speaks in haikus.\n\n{input}")
            >>> model = "llama-3.1-8b-instruct"
            >>> chat_response = csi.chat(model, [msg], ChatParams(max_tokens=64))
        """

    def select_language(self, text: str, languages: list[Language]) -> Language | None:
        """Select the detected language for the provided input based on the list of possible languages.
            If no language matches, None is returned.

        Parameters:
            text (str, required): Text input.
            languages (list[Language], required): All languages that should be considered during detection.

        Examples:
            >>> text = "Ich spreche Deutsch nur ein bisschen."
            >>> languages = [Language.ENG, Language.DEU]
            >>> result = csi.select_language(text, languages)
        """

    def complete_all(self, requests: list[CompletionRequest]) -> list[Completion]:
        """Generates several completions potentially in parallel. Returns as soon as all completions are ready.

        Parameters:
            requests (list[CompletionRequest], required): List of completion requests.

        Examples:
            >>> params = CompletionParams(max_tokens=64)
            >>> request_1 = CompletionRequest(model, "Say hello to Alice", params)
            >>> request_2 = CompletionRequest(model, "Say hello to Bob", params)
            >>> result = csi.complete_all([request_1, request_2])
            >>> len(result) # 2
            >>> "Alice" in result[0].text # True
            >>> "Bob" in result[1].text # True
        """

    def search(
        self,
        index_path: IndexPath,
        query: str,
        max_results: int = 1,
        min_score: float | None = None,
    ) -> list[SearchResult]:
        """Search in a document index.

        Parameters:
            index_path (IndexPath, required): Index path in the document index to access.
            query (str, required): Text to be search for.
            max_results (int, required): Maximal number of results.
            min_score (float, optional, Default NoneNone): Minimal score for result to be included.

        Examples:
            >>> index_path = IndexPath("f13", "wikipedia-de", "luminous-base-asymmetric-64")
            >>> query = "What is the population of Heidelberg?"
            >>> result = csi.search(index_path, query)
            >>> r0 = result[0]
            >>> "Heidelberg" in r0.content, "Heidelberg" in r0.document_path.name # True, True
        """
