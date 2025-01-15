import json

from .csi import (
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
    JsonSerializable,
    Language,
    Message,
    Role,
    SearchResult,
)
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


def chat_params_wit(chat_params: ChatParams) -> WitChatParams:
    return WitChatParams(
        max_tokens=chat_params.max_tokens,
        temperature=chat_params.temperature,
        top_p=chat_params.top_p,
    )


def completion_from_wit(completion: WitCompletion) -> Completion:
    return Completion(
        text=completion.text,
        finish_reason=finish_reason_from_wit(completion.finish_reason),
    )


def completion_params_wit(
    completion_params: CompletionParams,
) -> WitCompletionParams:
    return WitCompletionParams(
        return_special_tokens=completion_params.return_special_tokens,
        max_tokens=completion_params.max_tokens,
        temperature=completion_params.temperature,
        top_k=completion_params.top_k,
        top_p=completion_params.top_p,
        stop=completion_params.stop,
    )


def completion_request_wit(
    completion_request: CompletionRequest,
) -> WitCompletionRequest:
    return WitCompletionRequest(
        model=completion_request.model,
        prompt=completion_request.prompt,
        params=completion_params_wit(completion_request.params),
    )


def finish_reason_from_wit(reason: WitFinishReason) -> FinishReason:
    match reason:
        case WitFinishReason.STOP:
            return FinishReason.STOP
        case WitFinishReason.LENGTH:
            return FinishReason.LENGTH
        case WitFinishReason.CONTENT_FILTER:
            return FinishReason.CONTENT_FILTER


def role_wit(role: Role) -> WitRole:
    match role:
        case Role.User:
            return WitRole.USER
        case Role.Assistant:
            return WitRole.ASSISTANT
        case Role.System:
            return WitRole.SYSTEM


def role_from_wit(role: WitRole) -> Role:
    match role:
        case WitRole.USER:
            return Role.User
        case WitRole.ASSISTANT:
            return Role.Assistant
        case WitRole.SYSTEM:
            return Role.System


def message_wit(message: Message) -> WitMessage:
    return WitMessage(role=role_wit(message.role), content=message.content)


def message_from_wit(msg: WitMessage) -> Message:
    return Message(role=role_from_wit(msg.role), content=msg.content)


def chat_response_from_wit(response: WitChatResponse) -> ChatResponse:
    return ChatResponse(
        message=message_from_wit(response.message),
        finish_reason=finish_reason_from_wit(response.finish_reason),
    )


def document_path_from_wit(document_path: WitDocumentPath) -> DocumentPath:
    return DocumentPath(
        namespace=document_path.namespace,
        collection=document_path.collection,
        name=document_path.name,
    )


def search_result_from_wit(result: WitSearchResult) -> SearchResult:
    return SearchResult(
        document_path=document_path_from_wit(result.document_path),
        content=result.content,
        score=result.score,
    )


def document_path_wit(document_path: DocumentPath) -> WitDocumentPath:
    return WitDocumentPath(
        namespace=document_path.namespace,
        collection=document_path.collection,
        name=document_path.name,
    )


def index_path_wit(index_path: IndexPath) -> WitIndexPath:
    return WitIndexPath(
        namespace=index_path.namespace,
        collection=index_path.collection,
        index=index_path.index,
    )


def chunk_params_wit(chunk_params: ChunkParams) -> WitChunkParams:
    return WitChunkParams(model=chunk_params.model, max_tokens=chunk_params.max_tokens)


def language_wit(language: Language) -> WitLanguage:
    match language:
        case Language.ENG:
            return WitLanguage.ENG
        case Language.DEU:
            return WitLanguage.DEU


def language_from_wit(language: WitLanguage) -> Language:
    match language:
        case WitLanguage.ENG:
            return Language.ENG
        case WitLanguage.DEU:
            return Language.DEU


class WasiCsi(Csi):
    def complete_all(self, requests: list[CompletionRequest]) -> list[Completion]:
        wit_requests = [completion_request_wit(request) for request in requests]
        wit_completions = wit_csi.complete(wit_requests)
        return [
            completion_from_wit(wit_completion) for wit_completion in wit_completions
        ]

    def chunk(self, text: str, params: ChunkParams) -> list[str]:
        wit_chunk_params = chunk_params_wit(params)
        return wit_csi.chunk(text, wit_chunk_params)

    def chat(
        self, model: str, messages: list[Message], params: ChatParams
    ) -> ChatResponse:
        wit_messages = [message_wit(message) for message in messages]
        wit_chat_params = chat_params_wit(params)
        response = wit_csi.chat(model, wit_messages, wit_chat_params)
        return chat_response_from_wit(response)

    def select_language(self, text: str, languages: list[Language]) -> Language | None:
        wit_languages = [language_wit(language) for language in languages]
        wit_language = wit_csi.select_language(text, wit_languages)
        if wit_language is None:
            return None
        return language_from_wit(wit_language)

    def search(
        self,
        index_path: IndexPath,
        query: str,
        max_results: int = 1,
        min_score: float | None = None,
    ) -> list[SearchResult]:
        wit_index_path = index_path_wit(index_path)
        return [
            search_result_from_wit(search_result)
            for search_result in wit_csi.search(
                wit_index_path, query, max_results, min_score
            )
        ]

    def document_metadata_all(
        self, requests: list[DocumentPath]
    ) -> list[JsonSerializable]:
        wit_requests = [document_path_wit(request) for request in requests]
        responses = wit_csi.document_metadata(wit_requests)
        return [
            json.loads(maybe_metadata) if maybe_metadata else None
            for maybe_metadata in responses
        ]
