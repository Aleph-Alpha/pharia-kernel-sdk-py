import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
    SpanExporter,
    SpanExportResult,
)
from opentelemetry.trace import StatusCode

from pharia_skill import (
    ChatParams,
    ChunkParams,
    CompletionParams,
    CompletionRequest,
    Csi,
    IndexPath,
    Language,
    Message,
)
from pharia_skill.testing import DevCsi


@pytest.fixture(scope="module")
def csi() -> Csi:
    return DevCsi()


@pytest.fixture(scope="module")
def model() -> str:
    return "llama-3.1-8b-instruct"


@pytest.mark.kernel
def test_complete(csi: Csi, model: str):
    params = CompletionParams(max_tokens=64)
    result = csi.complete(model, "Say hello to Bob", params)
    assert "Bob" in result.text


@pytest.mark.kernel
def test_chat(csi: Csi, model: str):
    params = ChatParams(max_tokens=64)
    messages = [Message.user("Say hello to Bob")]
    result = csi.chat(model, messages, params)
    assert "Bob" in result.message.content


@pytest.mark.kernel
def test_chunk(csi: Csi, model: str):
    text = "A very very very long text that can be chunked."
    params = ChunkParams(model, max_tokens=1)
    result = csi.chunk(text, params)
    assert len(result) == 13


@pytest.mark.kernel
def test_select_language(csi: Csi):
    text = "Ich spreche Deutsch nur ein bisschen."
    languages = [Language.ENG, Language.DEU]
    result = csi.select_language(text, languages)
    assert result == Language.DEU


@pytest.mark.kernel
def test_complete_all(csi: Csi, model: str):
    params = CompletionParams(max_tokens=64)
    request_1 = CompletionRequest(model, "Say hello to Alice", params)
    request_2 = CompletionRequest(model, "Say hello to Bob", params)
    result = csi.complete_all([request_1, request_2])
    assert len(result) == 2
    assert "Alice" in result[0].text
    assert "Bob" in result[1].text


@pytest.mark.kernel
def test_search(csi: Csi):
    # Given an existing index
    index_path = IndexPath("f13", "wikipedia-de", "luminous-base-asymmetric-64")
    query = "What is the population of Heidelberg?"

    # When searching
    result = csi.search(index_path, query)

    # Then we get a result
    assert len(result) == 1
    assert "Heidelberg" in result[0].content
    assert "Heidelberg" in result[0].document_path.name


class InMemorySpanExporter(SpanExporter):
    def __init__(self):
        self.finished_spans = []

    def export(self, spans):
        self.finished_spans.extend(spans)
        return SpanExportResult.SUCCESS

    def shutdown(self):
        self.finished_spans.clear()


@pytest.fixture
def exporter() -> InMemorySpanExporter:
    trace_provider = TracerProvider()
    trace.set_tracer_provider(trace_provider)

    exporter = InMemorySpanExporter()
    span_processor = SimpleSpanProcessor(exporter)
    trace_provider.add_span_processor(span_processor)
    return exporter


def test_tracing(exporter: InMemorySpanExporter):
    # Given a csi setup with an in-memory exporter
    csi = DevCsi()

    # When running a completion request
    csi.complete(
        "llama-3.1-8b-instruct", "Say hello to Bob", CompletionParams(max_tokens=64)
    )

    # Then the exporter has received a successful span
    assert len(exporter.finished_spans) == 1
    assert exporter.finished_spans[0].status.status_code == StatusCode.OK

    # And the input and output are set as attributes
    assert "Say hello to Bob" in exporter.finished_spans[0].attributes["input"]
    assert "Bob" in exporter.finished_spans[0].attributes["output"]
