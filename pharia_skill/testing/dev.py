"""
DevCsi can be used for testing Skill code locally against a running Pharia Kernel.
"""

import json
import os
from dataclasses import asdict
from typing import Any, Protocol

import requests
from dotenv import load_dotenv
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
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
    IndexPath,
    Language,
    Message,
    SearchResult,
)
from pharia_skill.studio import StudioClient, StudioExporter, StudioSpanProcessor


class CsiClient(Protocol):
    def run(self, function: str, data: dict) -> Any: ...


class HttpClient(CsiClient):
    """Make requests with a given payload against a running Pharia Kernel."""

    VERSION = "0.2"

    def __init__(self):
        load_dotenv()
        self.url = os.environ["PHARIA_KERNEL_ADDRESS"] + "/csi"
        token = os.environ["PHARIA_AI_TOKEN"]
        self.session = requests.Session()
        self.session.headers = {"Authorization": f"Bearer {token}"}

    def __del__(self):
        if hasattr(self, "session"):
            self.session.close()

    def run(self, function: str, data: dict) -> dict:
        response = self.session.post(
            self.url, json={"version": self.VERSION, "function": function, **data}
        )
        response.raise_for_status()
        return response.json()


class DevCsi(Csi):
    """
    DevCsi can be used for testing Skill code locally against a running Pharia Kernel.

    This implementation of Cognitive System Interface (CSI) is backed by a running instance of Pharia Kernel via HTTP.
    This enables skill developers to run and test skills against the same services that are used by the Pharia Kernel.

    The following environment variables are required:

    * `PHARIA_AI_TOKEN` (Pharia AI token)
    * `PHARIA_KERNEL_ADDRESS` (Pharia Kernel endpoint; example: "https://pharia-kernel.aleph-alpha.stackit.run")

    If you want to export traces to Pharia Studio, also set:

    * `PHARIA_STUDIO_ADDRESS` (Pharia Studio endpoint; example: "https://pharia-studio.aleph-alpha.stackit.run")
    """

    def __init__(self):
        self.client: CsiClient = HttpClient()

    @classmethod
    def with_studio(cls, project: str) -> "DevCsi":
        """Create a `DevCsi` that exports traces to Pharia Studio.

        This function creates a `StudioExporter` and registers it with the tracer provider.
        The exporter uploads spans once the root span ends.

        Args:
            project: The name of the studio project to export traces to. Will be created if it does not exist.
        """
        csi = cls()
        client = StudioClient.with_project(project)
        exporter = StudioExporter(client)
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
            if isinstance(processor, StudioSpanProcessor):
                processor.span_exporter = exporter
                return

        span_processor = StudioSpanProcessor(exporter)
        provider.add_span_processor(span_processor)

    @classmethod
    def existing_exporter(cls) -> StudioExporter | None:
        """Return the first studio exporter attached to the provider, if any."""
        provider = cls.provider()
        for processor in provider._active_span_processor._span_processors:
            if isinstance(processor, StudioSpanProcessor):
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

    def run(self, function: str, data: dict):
        with trace.get_tracer(__name__).start_as_current_span(function) as span:
            span.set_attribute("input", json.dumps(data))
            try:
                output = self.client.run(function, data)
            except Exception as e:
                span.set_status(StatusCode.ERROR, str(e))
                raise e
            span.set_status(StatusCode.OK)
            span.set_attribute("output", json.dumps(output))

        return output

    def complete(self, model: str, prompt: str, params: CompletionParams) -> Completion:
        data = {
            "prompt": prompt,
            "model": model,
            "params": asdict(params),
        }
        output = self.run(self.complete.__name__, data)
        return Completion(**output)

    def chunk(self, text: str, params: ChunkParams) -> list[str]:
        data = {
            "text": text,
            "params": asdict(params),
        }
        return self.run(self.chunk.__name__, data)  # type: ignore

    def chat(
        self, model: str, messages: list[Message], params: ChatParams
    ) -> ChatResponse:
        data = {
            "model": model,
            "messages": [asdict(m) for m in messages],
            "params": asdict(params),
        }
        output = self.run(self.chat.__name__, data)
        return ChatResponse.from_dict(output)

    def select_language(self, text: str, languages: list[Language]) -> Language | None:
        data = {
            "text": text,
            "languages": [language.name.lower() for language in languages],
        }
        output = self.run(self.select_language.__name__, data)
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
        output = self.run(self.complete_all.__name__, data)
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
        output = self.run(self.search.__name__, data)
        return [
            SearchResult(
                document_path=DocumentPath(**result["document_path"]),
                content=result["content"],
                score=result["score"],
            )
            for result in output
        ]
