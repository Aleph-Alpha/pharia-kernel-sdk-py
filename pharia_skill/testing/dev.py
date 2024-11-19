"""
DevCsi can be used for testing Skill code locally against a running Pharia Kernel.
"""

import json
import os
from dataclasses import asdict

import requests
from dotenv import load_dotenv
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
)
from opentelemetry.trace import StatusCode

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
from pharia_skill.studio import StudioClient, StudioExporter


def chat_response_from_dict(body: dict) -> ChatResponse:
    return ChatResponse(
        message=Message(**body["message"]),
        finish_reason=FinishReason(body["finish_reason"]),
    )


class DevCsi(Csi):
    """
    DevCsi can be used for testing Skill code locally against a running Pharia Kernel.

    This implementation of Cognitive System Interface (CSI) is backed by a running instance of Pharia Kernel via HTTP.
    This enables skill developers to run and test skills against the same services that are used by the Pharia Kernel.

    The following environment variables are required:

    * `AA_API_TOKEN` (Aleph Alpha API token)
    * `PHARIA_KERNEL_ADDRESS` (Pharia Kernel endpoint; example: "https://pharia-kernel.aleph-alpha.stackit.run")

    If you want to export traces to Pharia Studio, also set:

    * `PHARIA_STUDIO_ADDRESS` (Pharia Studio endpoint; example: "https://pharia-studio.aleph-alpha.stackit.run")
    """

    VERSION = "0.2"

    def __init__(self):
        load_dotenv()
        self.url = os.environ["PHARIA_KERNEL_ADDRESS"] + "/csi"
        token = os.environ["AA_API_TOKEN"]
        self.session = requests.Session()
        self.session.headers = {"Authorization": f"Bearer {token}"}
        self.exporter: StudioExporter | None = None

    def __del__(self):
        if hasattr(self, "session"):
            self.session.close()

    @classmethod
    def with_studio(cls, project: str) -> "DevCsi":
        """Create a `DevCsi` that exports traces to Pharia Studio.

        This function creates a `StudioExporter` and registers it with the tracer provider.
        The exporter uploads spans once the root span ends.

        Args:
            project: The name of the studio project to export traces to. Will be created if it does not exist.
        """
        csi = cls()
        exporter = StudioExporter(StudioClient(project))
        csi.set_span_exporter(exporter)
        return csi

    @classmethod
    def set_span_exporter(cls, exporter: StudioExporter):
        """Set a span exporter for Studio if it has not been set yet.

        This method overwrites any existing exporters, thereby ensuring that there
        are never two exporters to Studio attached at the same time.
        """
        provider = cls.provider()
        for processor in provider._active_span_processor._span_processors:
            if isinstance(processor, SimpleSpanProcessor):
                processor.span_exporter = exporter
                return

        span_processor = SimpleSpanProcessor(exporter)
        provider.add_span_processor(span_processor)

    @classmethod
    def existing_exporter(cls) -> StudioExporter | None:
        """Return the first studio exporter attached to the provider, if any."""
        provider = cls.provider()
        for processor in provider._active_span_processor._span_processors:
            if isinstance(processor, SimpleSpanProcessor):
                if isinstance(processor.span_exporter, StudioExporter):
                    return processor.span_exporter
        return None

    @staticmethod
    def provider() -> TracerProvider:
        """Tracer provider for the current thread.

        Check if the tracer provider is already set and if not, set it.
        """
        if not isinstance(trace.get_tracer_provider(), TracerProvider):
            trace_provider = TracerProvider()
            trace.set_tracer_provider(trace_provider)

        return trace.get_tracer_provider()  # type: ignore

    def request(self, function: str, data: dict):
        with trace.get_tracer(__name__).start_as_current_span(function) as span:
            span.set_attribute("type", "TASK_SPAN")
            span.set_attribute("input", json.dumps(data))

            data["version"] = self.VERSION
            data["function"] = function
            response = self.session.post(self.url, json=data)
            if response.status_code != 200:
                span.set_status(StatusCode.ERROR, response.text)
                raise Exception(f"{response.status_code}: {response.text}")
            output = response.json()
            span.set_status(StatusCode.OK)
            span.set_attribute("output", json.dumps(output))

        return output

    def complete(self, model: str, prompt: str, params: CompletionParams) -> Completion:
        data = {
            "prompt": prompt,
            "model": model,
            "params": asdict(params),
        }
        output = self.request(self.complete.__name__, data)
        return Completion(**output)

    def chunk(self, text: str, params: ChunkParams) -> list[str]:
        data = {
            "text": text,
            "params": asdict(params),
        }
        return self.request(self.chunk.__name__, data)  # type: ignore

    def chat(
        self, model: str, messages: list[Message], params: ChatParams
    ) -> ChatResponse:
        data = {
            "model": model,
            "messages": [asdict(m) for m in messages],
            "params": asdict(params),
        }
        output = self.request(self.chat.__name__, data)
        return chat_response_from_dict(output)

    def select_language(self, text: str, languages: list[Language]) -> Language | None:
        data = {
            "text": text,
            "languages": [language.name.lower() for language in languages],
        }
        output = self.request(self.select_language.__name__, data)
        match output:
            case "eng":
                return Language.ENG
            case "deu":
                return Language.DEU
            case _:
                return None

    def complete_all(self, requests: list[CompletionRequest]) -> list[Completion]:
        data = {
            "requests": [asdict(request) for request in requests],
        }
        output = self.request(self.complete_all.__name__, data)
        return [Completion(**completion) for completion in output]

    def search(
        self,
        index_path: IndexPath,
        query: str,
        max_results: int = 1,
        min_score: float | None = None,
    ) -> list[SearchResult]:
        data = {
            "index_path": asdict(index_path),
            "query": query,
            "max_results": max_results,
            "min_score": min_score,
        }
        output = self.request(self.search.__name__, data)
        return [
            SearchResult(
                document_path=DocumentPath(**result["document_path"]),
                content=result["content"],
                score=result["score"],
            )
            for result in output
        ]
