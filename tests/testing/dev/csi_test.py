import json
from typing import Sequence
from unittest.mock import Mock, patch

import pytest
import requests

from pharia_skill import (
    ChatParams,
    ChatStreamResponse,
    ChunkParams,
    CompletionParams,
    Csi,
    Document,
    DocumentPath,
    FinishReason,
    Granularity,
    IndexPath,
    InvokeRequest,
    Language,
    Message,
    Role,
    Text,
    Tool,
    ToolError,
    ToolOutput,
)
from pharia_skill.studio import (
    SpanClient,
    StudioExporter,
    StudioSpan,
)
from pharia_skill.testing import DevCsi, MessageRecorder, StubCsi
from pharia_skill.testing.dev.client import Client


@pytest.fixture(scope="module")
def csi() -> Csi:
    return DevCsi()


@pytest.fixture(scope="module")
def csi_with_test_namespace() -> Csi:
    """The `test-beta` namespace is configured with hardcoded tools."""
    return DevCsi(namespace="test-beta")


@pytest.fixture
def given_document() -> DocumentPath:
    """The tests suite expects a document `kernel-docs` in the `test` collection of the `Kernel` index."""
    return DocumentPath("Kernel", "test", "kernel-docs")


@pytest.fixture
def given_index() -> IndexPath:
    """The tests suite expects an index `asym-64` in the `test` collection of the `Kernel` index."""
    return IndexPath("Kernel", "test", "asym-64")


@pytest.mark.kernel
def test_invoke_tool(csi_with_test_namespace: Csi):
    result = csi_with_test_namespace.invoke_tool("add", a=1, b=2)
    assert result.contents == ["3"]


@pytest.mark.kernel
def test_invoke_saboteur_tool(csi_with_test_namespace: Csi):
    with pytest.raises(ToolError) as excinfo:
        csi_with_test_namespace.invoke_tool("saboteur", a=1, b=2)

    assert "Out of cheese." in str(excinfo.value)


@pytest.mark.kernel
def test_invoke_tool_concurrent(csi_with_test_namespace: Csi):
    # Given a list of invoke requests
    requests = [
        InvokeRequest(name="add", arguments={"a": 1, "b": 2}),
        InvokeRequest(name="saboteur", arguments={"a": 1, "b": 2}),
    ]

    # When invoking the tools concurrently
    results = csi_with_test_namespace.invoke_tool_concurrent(requests)

    # Then the results contain one success and one error
    assert len(results) == 2
    assert isinstance(results[0], ToolOutput)
    assert isinstance(results[1], ToolError)


@pytest.mark.kernel
def test_list_tools(csi_with_test_namespace: Csi):
    tools = csi_with_test_namespace.list_tools()
    assert len(tools) == 3
    assert tools[0].name == "add"
    assert tools[1].name == "saboteur"
    assert tools[2].name == "subtract"


@pytest.mark.kernel
def test_completion_stream(csi: Csi, model: str):
    params = CompletionParams(max_tokens=64)
    response = csi._completion_stream(model, "Say hello to Bob", params)

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
    message = csi.chat_stream_step(model, messages, params=params)

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
def test_chat_stream_skip_streaming_message(csi: Csi, model: str):
    params = ChatParams(max_tokens=64)
    messages = [Message.user("Say hello to Bob")]
    message = csi.chat_stream_step(model, messages, params=params)

    assert message.finish_reason() == FinishReason.STOP
    usage = message.usage()
    assert usage.prompt == 14
    assert usage.completion == 9


@pytest.mark.kernel
def test_chat_stream_after_consumed(csi: Csi, model: str):
    params = ChatParams(max_tokens=64)
    messages = [Message.user("Say hello to Bob")]
    message = csi.chat_stream_step(model, messages, params=params)

    assert message.finish_reason() == FinishReason.STOP
    with pytest.raises(RuntimeError) as excinfo:
        next(message.stream())
    assert "The stream has already been consumed" == str(excinfo.value)


@pytest.mark.kernel
def test_chat_stream_with_tool(csi_with_test_namespace: Csi):
    model = "llama-3.3-70b-instruct"
    system = Message.system(
        'DO NOT use quotes (") for integer values when calling tools. i.e. `"parameters": {"a": 1}`'
    )
    user = Message.user("What is 1 + 2?")
    messages = [system, user]

    recorder = MessageRecorder[None]()
    with csi_with_test_namespace.chat_stream(
        model, messages, tools=["add"]
    ) as response:
        recorder.forward_response(response)

    recorded_messages = recorder.messages()

    assert len(recorded_messages) == 1
    assert recorded_messages[0].role == "assistant"
    assert recorded_messages[0].content == "The answer is 3."


@pytest.mark.kernel
def test_chat_stream_with_saboteur_tool(csi_with_test_namespace: Csi, model: str):
    messages = [Message.user("Return response directly")]

    recorder = MessageRecorder[None]()
    with csi_with_test_namespace.chat_stream(
        model, messages, tools=["saboteur"]
    ) as response:
        recorder.forward_response(response)

    recorded_messages = recorder.messages()

    assert len(recorded_messages) == 1
    assert recorded_messages[0].role == "assistant"
    assert "out of cheese" in recorded_messages[0].content.lower()


@pytest.mark.kernel
def test_complete(csi: Csi, model: str):
    params = CompletionParams(max_tokens=64)
    result = csi.complete(model, "Say hello to Bob", params)
    assert "Bob" in result.text
    assert isinstance(result.finish_reason, FinishReason)


@pytest.mark.kernel
def test_complete_echo(csi: Csi, model: str):
    params = CompletionParams(max_tokens=1, echo=True)
    result = csi.complete(model, "An apple a day", params)
    assert result.text == "An apple a day keeps"
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
@pytest.mark.studio
def test_multiple_csi_instances_do_not_duplicate_exporters():
    """A user might use different `DevCsi` instances in the same process.

    Assert that the processors are not duplicated.
    """
    # Given two csi instances
    csi1 = DevCsi(project="kernel-test")
    csi2 = DevCsi(project="kernel-test")

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
def test_stream_error_event_is_raised():
    # Given a completion request against a non-existing model
    csi = DevCsi()
    params = CompletionParams(max_tokens=64)
    stream = csi._completion_stream("non-existing-model", "Say hello to Bob", params)

    # When calling next
    with pytest.raises(ValueError) as e:
        stream.next()

    # Then an error with a good error message is raised
    assert (
        str(e.value)
        == "The Skill tried to access a model that was not found. Please check the provided model name. You can query the list of available models at the `models` endpoint of the inference API. If you believe the model should be available, contact the operator of your PhariaAI instance."
    )


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
    assert 'Original Error: {"error": "csi-version"}' in str(e.value)


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
    assert "Original Error: {'error': 'csi-version'}" in str(e.value)


def test_tools_are_added_to_system_prompt():
    # Given a spy csi that stores the messages
    class SpyCsi(StubCsi):
        def __init__(self) -> None:
            self.messages: list[Message] = []

        def _chat_stream(
            self,
            model: str,
            messages: list[Message],
            params: ChatParams,
        ) -> ChatStreamResponse:
            self.messages = messages
            return super()._chat_stream(model, messages, params)

    csi = SpyCsi()

    # When calling chat with tools
    fish_counter = Tool(
        name="fish-count",
        description="Count the number of fish in the sea",
        input_schema={"fish-type": {"type": "string"}},
    )
    messages = [Message.user("How many fish left in the sea?")]
    csi.chat_stream_step("gpt-nautilus", messages, tools=[fish_counter])

    # Then the tools are added to the system prompt
    system = csi.messages[0]
    assert system.role == Role.System
    assert "fish-count" in system.content


# Although this test does not talk to the Kernel, it relies on the two environment
# variables `PHARIA_AI_TOKEN` and `PHARIA_KERNEL_ADDRESS` to be set to construct the
# `Client` instance.
@pytest.mark.kernel
def test_listing_tools_without_namespace_raises_error():
    # Given a csi without a namespace
    csi = DevCsi()

    # When listing the tools
    with pytest.raises(ValueError) as e:
        csi.list_tools()

    # Then an error is raised
    assert "Specifying a namespace when constructing" in str(e.value)
