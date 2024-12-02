from dataclasses import asdict
from typing import Sequence

import pytest

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
from pharia_skill.studio import (
    SpanClient,
    StudioExporter,
    StudioSpan,
)
from pharia_skill.testing.dev import DevCsi, HttpClient


@pytest.fixture(scope="module")
def csi() -> Csi:
    return DevCsi()


@pytest.fixture(scope="module")
def model() -> str:
    return "llama-3.1-8b-instruct"


@pytest.mark.kernel
def test_http_client_run(model: str):
    client = HttpClient()
    params = CompletionParams(max_tokens=1)

    result = client.run(
        "complete",
        {
            "model": model,
            "prompt": "Say hello to Bob",
            "params": asdict(params),
        },
    )
    assert result.get("text") is not None


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
    index_path = IndexPath("Kernel", "test", "asym-64")
    query = "What is the Kernel?"

    # When searching
    result = csi.search(index_path, query)

    # Then we get a result
    assert len(result) == 1
    assert "Kernel" in result[0].content
    assert "kernel" in result[0].document_path.name


class StubStudioClient(SpanClient):
    def submit_spans(self, spans: Sequence[StudioSpan]):
        pass


@pytest.mark.kernel
def test_set_trace_exporter():
    # Given a fresh CSI
    csi = DevCsi()

    # When setting an exporter
    exporter = StudioExporter(StubStudioClient())
    csi.set_span_exporter(exporter)

    # Then the exporter is set
    assert csi.existing_exporter() == exporter


@pytest.mark.kernel
def test_set_same_trace_exporter_twice_does_not_raise():
    # Given a csi with one exporter set
    csi = DevCsi()
    exporter = StudioExporter(StubStudioClient())
    csi.set_span_exporter(exporter)

    # When setting the same exporter again
    csi.set_span_exporter(exporter)

    # Then the number of processors is still one
    assert len(csi.provider()._active_span_processor._span_processors) == 1


@pytest.mark.kernel
def test_set_different_trace_exporter_raises():
    # Given a csi with one exporter set
    csi = DevCsi()
    exporter_1 = StudioExporter(StubStudioClient())
    csi.set_span_exporter(exporter_1)

    # Then setting a different exporter overwrites the existing one
    exporter_2 = StudioExporter(StubStudioClient())
    csi.set_span_exporter(exporter_2)

    # And the new exporter is the one that is set
    assert csi.existing_exporter() == exporter_2
    assert len(csi.provider()._active_span_processor._span_processors) == 1


@pytest.mark.kernel
def test_multiple_csi_instances_do_not_duplicate_exporters():
    """A user might use different `DevCsi` instances in the same process.

    Assert that the processors are not duplicated.
    """
    # Given two csi instances
    csi1 = DevCsi.with_studio(project="kernel-test")
    csi2 = DevCsi.with_studio(project="kernel-test")

    # Then only one exporter is attached
    assert len(csi1.provider()._active_span_processor._span_processors) == 1
    assert len(csi2.provider()._active_span_processor._span_processors) == 1
