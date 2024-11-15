"""
This module exposes the interfaces for skills to interact with the Pharia Kernel
via the Cognitive System Interface (CSI).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol

from .wit.imports import csi as wit_csi
from .wit.imports.csi import ChatParams as WitChatParams
from .wit.imports.csi import ChatResponse as WitChatResponse
from .wit.imports.csi import ChunkParams as WitChunkParams
from .wit.imports.csi import Completion as WitCompletion
from .wit.imports.csi import CompletionParams as WitCompletionParams
from .wit.imports.csi import CompletionRequest as WitCompletionRequest
from .wit.imports.csi import DocumentPath as WitDocumentPath
from .wit.imports.csi import FinishReason as WitFinishReason
from .wit.imports.csi import IndexPath as WitIndexPath
from .wit.imports.csi import Language as WitLanguage
from .wit.imports.csi import Message as WitMessage
from .wit.imports.csi import Role as WitRole
from .wit.imports.csi import SearchResult as WitSearchResult

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

    @classmethod
    def from_wit(cls, reason: WitFinishReason) -> "FinishReason":
        match reason:
            case WitFinishReason.STOP:
                return FinishReason.STOP
            case WitFinishReason.LENGTH:
                return FinishReason.LENGTH
            case WitFinishReason.CONTENT_FILTER:
                return FinishReason.CONTENT_FILTER


@dataclass
class Completion:
    """The result of a completion, including the text generated as well as
    why the model finished completing.

    text (str, required): The text generated by the model,
    finish-reason : The reason the model finished generating
    """

    text: str
    finish_reason: FinishReason

    @classmethod
    def from_wit(cls, completion: WitCompletion) -> "Completion":
        return cls(
            text=completion.text,
            finish_reason=FinishReason.from_wit(completion.finish_reason),
        )


@dataclass
class CompletionRequest:
    """Completion request request parameters for complete_all

    Attributes:
        model (str, required): Name of model to use.
        prompt (str, required): The text to be completed.
        params (CompletionParams, required): Parameters for the requested completion.
    """

    model: str
    prompt: str
    params: CompletionParams


@dataclass
class ChatParams(WitChatParams):
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

    @property
    def wit(self) -> WitRole:
        match self:
            case Role.User:
                return WitRole.USER
            case Role.Assistant:
                return WitRole.ASSISTANT
            case Role.System:
                return WitRole.SYSTEM

    @classmethod
    def from_wit(cls, role: WitRole) -> "Role":
        match role:
            case WitRole.USER:
                return Role.User
            case WitRole.ASSISTANT:
                return Role.Assistant
            case WitRole.SYSTEM:
                return Role.System


@dataclass
class Message:
    """Describes a message in a chat.

    Parameters:
        role (Role, required): The role of the message.
        content (str, required): The content of the message.
    """

    role: Role
    content: str

    @property
    def wit(self) -> WitMessage:
        return WitMessage(role=self.role.wit, content=self.content)

    @classmethod
    def from_wit(cls, msg: WitMessage) -> "Message":
        return cls(role=Role.from_wit(msg.role), content=msg.content)

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

    @classmethod
    def from_wit(cls, res: WitChatResponse) -> "ChatResponse":
        return cls(
            message=Message.from_wit(res.message),
            finish_reason=FinishReason.from_wit(res.finish_reason),
        )

    @classmethod
    def from_dict(cls, body: dict) -> "ChatResponse":
        return cls(
            message=Message(**body["message"]),
            finish_reason=FinishReason(body["finish_reason"]),
        )


@dataclass
class ChunkParams:
    """Chunking parameters

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

    @classmethod
    def from_wit(cls, res: WitDocumentPath) -> "DocumentPath":
        return cls(namespace=res.namespace, collection=res.collection, name=res.name)


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
        document_path (DocumentPath): The document_path that identifies the document
        content (str): The contents of the retrieved document
        score (float): the score representing the match regarding the search request
    """

    document_path: DocumentPath
    content: str
    score: float

    @classmethod
    def from_wit(cls, res: WitSearchResult) -> "SearchResult":
        return cls(
            document_path=DocumentPath.from_wit(res.document_path),
            content=res.content,
            score=res.score,
        )


@dataclass
class Language(int, Enum):
    """ISO 639-3 language

    Attributes:
        ENG (0): English
        DEU (1): German
    """

    ENG = 0
    DEU = 1

    @property
    def wit(self) -> WitLanguage:
        match self:
            case Language.ENG:
                return WitLanguage.ENG
            case Language.DEU:
                return WitLanguage.DEU

    @classmethod
    def from_wit(cls, language: WitLanguage) -> "Language":
        match language:
            case WitLanguage.ENG:
                return Language.ENG
            case WitLanguage.DEU:
                return Language.DEU


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
            text (str, required): text to be chunked
            params (ChunkParams, required): parameter used for chunking, model and maximal number of tokens

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
            messages (list[Message], required): List of messages, alternating between messages from user and system
            params (ChatParams, required): parameters used for the chat

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
            text (str, required): text input
            languages (list[Language], required): All languages that should be considered during detection.

        Examples:
            >>> text = "Ich spreche Deutsch nur ein bisschen."
            >>> languages = [Language.ENG, Language.DEU]
            >>> result = csi.select_language(text, languages)
        """

    def complete_all(self, requests: list[CompletionRequest]) -> list[Completion]:
        """Generates several completions potentially in parallel. Returns as soon as all completions are ready.

        Parameters:
            requests (list[CompletionRequest], required): list of completion requests.

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
        max_results: int,
        min_score: float | None,
    ) -> list[SearchResult]:
        """search in a document index

        Parameters:
            index_path (IndexPath, required): index path in the document index to access,
            query (str, required): text to be search for
            max_results (int, required): maximal number of results
            min_score (float, optional, Default NoneNone): minimal score for result to be included

        Examples:
            >>> index_path = IndexPath("f13", "wikipedia-de", "luminous-base-asymmetric-64")
            >>> query = "What is the population of Heidelberg?"
            >>> result = csi.search(index_path, query)
            >>> r0 = result[0]
            >>> "Heidelberg" in r0.content, "Heidelberg" in r0.document_path.name # True, True
        """


class WasiCsi(Csi):
    def complete(self, model: str, prompt: str, params: CompletionParams) -> Completion:
        wit_params = WitCompletionParams(
            max_tokens=params.max_tokens,
            temperature=params.temperature,
            top_k=params.top_k,
            top_p=params.top_p,
            stop=params.stop,
        )
        completion = wit_csi.complete(model, prompt, wit_params)
        return Completion.from_wit(completion)

    def chunk(self, text: str, params: ChunkParams) -> list[str]:
        return wit_csi.chunk(
            text, WitChunkParams(model=params.model, max_tokens=params.max_tokens)
        )

    def chat(
        self, model: str, messages: list[Message], params: ChatParams
    ) -> ChatResponse:
        response = wit_csi.chat(model, [m.wit for m in messages], params)
        return ChatResponse.from_wit(response)

    def select_language(self, text: str, languages: list[Language]) -> Language | None:
        wit_lang = wit_csi.select_language(text, [lang.wit for lang in languages])
        if wit_lang is None:
            return None
        return Language.from_wit(wit_lang)

    def complete_all(self, requests: list[CompletionRequest]) -> list[Completion]:
        completions = wit_csi.complete_all(
            [
                WitCompletionRequest(
                    request.model,
                    request.prompt,
                    params=WitCompletionParams(
                        max_tokens=request.params.max_tokens,
                        temperature=request.params.temperature,
                        top_k=request.params.top_k,
                        top_p=request.params.top_p,
                        stop=request.params.stop,
                    ),
                )
                for request in requests
            ]
        )
        return [Completion.from_wit(completion) for completion in completions]

    def search(
        self,
        index_path: IndexPath,
        query: str,
        max_results: int,
        min_score: float | None = None,
    ) -> list[SearchResult]:
        wit_index_path = WitIndexPath(
            namespace=index_path.namespace,
            collection=index_path.collection,
            index=index_path.index,
        )
        return [
            SearchResult.from_wit(search_result)
            for search_result in wit_csi.search(
                wit_index_path, query, max_results, min_score
            )
        ]
