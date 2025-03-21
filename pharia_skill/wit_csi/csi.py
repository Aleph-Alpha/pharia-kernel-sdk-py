import json
from typing import Generator

from pharia_skill.csi.chunking import Chunk
from pharia_skill.csi.inference import (
    ExplanationRequest,
    FinishReason,
    TextScore,
)

from ..csi import (
    ChatRequest,
    ChatResponse,
    ChunkRequest,
    Completion,
    CompletionDelta,
    CompletionParams,
    CompletionRequest,
    Csi,
    Document,
    DocumentPath,
    JsonSerializable,
    Language,
    SearchRequest,
    SearchResult,
    SelectLanguageRequest,
    StreamReport,
)
from ..wit.imports import chunking as wit_chunking
from ..wit.imports import document_index as wit_document_index
from ..wit.imports import inference as wit_inference
from ..wit.imports import language as wit_language
from .chunking import chunk_from_wit, chunk_request_to_wit
from .document_index import (
    document_from_wit,
    document_path_to_wit,
    search_request_to_wit,
    search_result_from_wit,
)
from .inference import (
    chat_request_to_wit,
    chat_response_from_wit,
    completion_delta_from_wit,
    completion_from_wit,
    completion_request_to_wit,
    explanation_request_to_wit,
    finish_reason_from_wit,
    text_score_from_wit,
    token_usage_from_wit,
)
from .language import language_from_wit, language_request_to_wit


class WitCsi(Csi):
    """Implementation of the Cognitive System Interface (CSI) that gets injected to skills at runtime.

    Responsible to tranlate between the types we expose in the SDK and the types in the `wit.imports` module,
    which are automatically generated from the WIT world via `componentize-py`.
    """

    def completion_stream(
        self, model: str, prompt: str, params: CompletionParams
    ) -> Generator[CompletionDelta, None, StreamReport]:
        request = completion_request_to_wit(CompletionRequest(model, prompt, params))
        stream = wit_inference.CompletionStream(request)
        finish_reason = FinishReason.STOP
        while (event := stream.next()) is not None:
            match event:
                case wit_inference.CompletionEvent_Delta:
                    yield completion_delta_from_wit(event.value)
                case wit_inference.CompletionEvent_Finished:
                    finish_reason = finish_reason_from_wit(event.value)
                case wit_inference.CompletionEvent_Usage:
                    usage = token_usage_from_wit(event.value)
                    return StreamReport(finish_reason, usage)
        raise Exception("completion_stream completed without receiving token usage")

    def complete_concurrent(
        self, requests: list[CompletionRequest]
    ) -> list[Completion]:
        wit_requests = [completion_request_to_wit(r) for r in requests]
        completions = wit_inference.complete(wit_requests)
        return [completion_from_wit(completion) for completion in completions]

    def chat_concurrent(self, requests: list[ChatRequest]) -> list[ChatResponse]:
        wit_requests = [chat_request_to_wit(r) for r in requests]
        responses = wit_inference.chat(wit_requests)
        return [chat_response_from_wit(response) for response in responses]

    def explain_concurrent(
        self, requests: list[ExplanationRequest]
    ) -> list[list[TextScore]]:
        wit_requests = [explanation_request_to_wit(r) for r in requests]
        responses = wit_inference.explain(wit_requests)
        return [
            [text_score_from_wit(score) for score in scores] for scores in responses
        ]

    def chunk_concurrent(self, requests: list[ChunkRequest]) -> list[list[Chunk]]:
        wit_requests = [chunk_request_to_wit(r) for r in requests]
        responses = wit_chunking.chunk_with_offsets(wit_requests)
        return [[chunk_from_wit(chunk) for chunk in response] for response in responses]

    def select_language_concurrent(
        self, requests: list[SelectLanguageRequest]
    ) -> list[Language | None]:
        wit_requests = [language_request_to_wit(r) for r in requests]
        languages = wit_language.select_language(wit_requests)
        return [
            language_from_wit(lang) if lang is not None else None for lang in languages
        ]

    def search_concurrent(
        self, requests: list[SearchRequest]
    ) -> list[list[SearchResult]]:
        wit_requests = [search_request_to_wit(r) for r in requests]
        results = wit_document_index.search(wit_requests)
        return [
            [search_result_from_wit(result) for result in results_per_request]
            for results_per_request in results
        ]

    def documents(self, document_paths: list[DocumentPath]) -> list[Document]:
        requests = [document_path_to_wit(path) for path in document_paths]
        documents = wit_document_index.documents(requests)
        return [document_from_wit(document) for document in documents]

    def documents_metadata(
        self, document_paths: list[DocumentPath]
    ) -> list[JsonSerializable]:
        requests = [document_path_to_wit(path) for path in document_paths]
        metadata = wit_document_index.document_metadata(requests)
        return [json.loads(metadata) if metadata else None for metadata in metadata]
