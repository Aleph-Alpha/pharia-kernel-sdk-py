import json
from typing import Sequence
from unittest.mock import Mock, patch

import pytest
import requests

from pharia_skill import (
    ChatParams,
    ChunkParams,
    CompletionParams,
    Csi,
    Document,
    DocumentPath,
    FinishReason,
    Granularity,
    IndexPath,
    Language,
    Message,
    Role,
    Text,
)
from pharia_skill.csi import inference as csi_inference
from pharia_skill.studio import (
    SpanClient,
    StudioExporter,
    StudioSpan,
)
from pharia_skill.testing.dev import DevCsi
from pharia_skill.testing.dev.client import Client


@pytest.fixture(scope="module")
def csi() -> Csi:
    return DevCsi()


@pytest.fixture
def given_document() -> DocumentPath:
    """The tests suite expects a document `kernel-docs` in the `test` collection of the `Kernel` index."""
    return DocumentPath("Kernel", "test", "kernel-docs")


@pytest.fixture
def given_index() -> IndexPath:
    """The tests suite expects an index `asym-64` in the `test` collection of the `Kernel` index."""
    return IndexPath("Kernel", "test", "asym-64")


@pytest.mark.kernel
def test_completion_stream(csi: Csi, model: str):
    params = CompletionParams(max_tokens=64)
    response = csi.completion_stream(model, "Say hello to Bob", params)

    stream = response.stream()
    assert next(stream).text is not None
    assert next(stream).text is not None
    assert response.finish_reason() == FinishReason.LENGTH
    usage = response.usage()
    assert usage.prompt == 4
    assert usage.completion == 64


@pytest.mark.kernel
def test_chat_stream(csi: Csi, model: str):
    params = ChatParams(max_tokens=64, logprobs="sampled")
    messages = [Message.user("Say hello to Bob")]
    message = csi.chat_stream(model, messages, params)

    assert message.role == "assistant"

    content = ""
    logprobs = []
    for m in message.stream():
        content += m.content
        logprobs += m.logprobs
    assert content == "Hello Bob! How are you today?"
    assert len(logprobs) == 9
    assert message.finish_reason() == FinishReason.STOP
    usage = message.usage()
    assert usage.prompt == 14
    assert usage.completion == 9


@pytest.mark.kernel
def test_chat_stream_full_message(csi: Csi, model: str):
    params = ChatParams(max_tokens=64, logprobs="sampled")
    messages = [Message.user("Say hello to Bob")]
    message = csi.chat_stream(model, messages, params)

    events = list(message.message())
    assert isinstance(events[0], csi_inference.MessageBegin)
    assert isinstance(events[1], csi_inference.MessageAppend)
    assert isinstance(events[2], csi_inference.FinishReason)
    assert isinstance(events[3], csi_inference.TokenUsage)


@pytest.mark.kernel
def test_chat_stream_skip_streaming_message(csi: Csi, model: str):
    params = ChatParams(max_tokens=64)
    messages = [Message.user("Say hello to Bob")]
    message = csi.chat_stream(model, messages, params)

    assert message.finish_reason() == FinishReason.STOP
    usage = message.usage()
    assert usage.prompt == 14
    assert usage.completion == 9


@pytest.mark.kernel
def test_chat_stream_after_consumed(csi: Csi, model: str):
    params = ChatParams(max_tokens=64)
    messages = [Message.user("Say hello to Bob")]
    message = csi.chat_stream(model, messages, params)

    assert message.finish_reason() == FinishReason.STOP
    with pytest.raises(RuntimeError) as excinfo:
        next(message.stream())
    assert "The stream has already been consumed" == str(excinfo.value)


@pytest.mark.kernel
def test_complete(csi: Csi, model: str):
    params = CompletionParams(max_tokens=64)
    result = csi.complete(model, "Say hello to Bob", params)
    assert "Bob" in result.text
    assert isinstance(result.finish_reason, FinishReason)


@pytest.mark.kernel
def test_chat(csi: Csi, model: str):
    params = ChatParams(max_tokens=64)
    messages = [Message.user("Say hello to Bob")]
    result = csi.chat(model, messages, params)
    assert "Bob" in result.message.content
    assert isinstance(result.message.role, Role)
    assert result.message.role == Role.Assistant


@pytest.mark.kernel
def test_explain(csi: Csi, model: str):
    scores = csi.explain(
        prompt="An apple a day",
        target=" keeps the doctor away",
        granularity=Granularity.WORD,
        model=model,
    )

    assert len(scores) == 4
    assert scores[0].start == 0
    assert scores[0].length == 2

    assert scores[1].start == 3
    assert scores[1].length == 5

    assert scores[2].start == 9
    assert scores[2].length == 1

    assert scores[3].start == 11
    assert scores[3].length == 3


@pytest.mark.kernel
def test_chunk(csi: Csi, model: str):
    text = "A very very very long text that can be chunked."
    params = ChunkParams(model, max_tokens=1)
    result = csi.chunk(text, params)
    assert len(result) == 13


@pytest.mark.kernel
def test_select_language(csi: Csi):
    text = "Ich spreche Deutsch nur ein bisschen."
    languages = [Language.English, Language.German]
    result = csi.select_language(text, languages)
    assert result == Language.German


@pytest.mark.kernel
def test_search(csi: Csi, given_index: IndexPath):
    query = "What is the Kernel?"

    # When searching
    result = csi.search(given_index, query)

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


@pytest.mark.kernel
def test_document_metadata(csi: Csi, given_document: DocumentPath):
    metadata = csi.document_metadata(given_document)
    assert isinstance(metadata, dict)
    assert metadata["url"] == "https://pharia-kernel.product.pharia.com/"


@pytest.mark.kernel
def test_documents(csi: Csi, given_document: DocumentPath):
    document = csi.document(given_document)

    assert isinstance(document, Document)
    assert document.path == given_document
    assert len(document.contents) == 1
    assert isinstance(document.contents[0], Text)
    assert document.text.startswith("You might be wondering")


@pytest.mark.kernel
@patch("requests.Session.post")
def test_text_error_response_used_on_json_decode_error(mock_post):
    # Given an http client that returns a 400 error that is not json
    client = Client()
    response = {"error": "csi-version"}
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.json.side_effect = requests.JSONDecodeError("msg", "msg", 0)
    mock_response.text = json.dumps(response)
    mock_post.return_value = mock_response

    # When doing a HTTP CSI request
    with pytest.raises(Exception) as e:
        client.run("complete", {})

    # Then the error message is forwarded
    assert str(e.value) == '400 Bad Request: {"error": "csi-version"}'


@pytest.mark.kernel
@patch("requests.Session.post")
def test_json_error_response_is_used(mock_post):
    # Given a http client that returns a 400 error with a json response
    client = Client()
    response = {"error": "csi-version"}
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.json.return_value = response
    mock_response.text = json.dumps(response)
    mock_post.return_value = mock_response

    # When doing a HTTP CSI request
    with pytest.raises(Exception) as e:
        client.run("complete", {})

    # Then the JSON is decoded in the error message
    assert str(e.value) == "400 Bad Request: {'error': 'csi-version'}"
