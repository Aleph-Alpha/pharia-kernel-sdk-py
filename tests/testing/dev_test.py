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
    params = ChunkParams(model=model, max_tokens=1)
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
    request_1 = CompletionRequest(
        model=model, prompt="Say hello to Alice", params=params
    )
    request_2 = CompletionRequest(model=model, prompt="Say hello to Bob", params=params)
    result = csi.complete_all([request_1, request_2])
    assert len(result) == 2
    assert "Alice" in result[0].text
    assert "Bob" in result[1].text


@pytest.mark.kernel
def test_search(csi: Csi):
    # Given an existing index
    index_path = IndexPath(
        namespace="f13", collection="wikipedia-de", index="luminous-base-asymmetric-64"
    )
    query = "What is the population of Heidelberg?"

    # When searching
    result = csi.search(index_path, query)

    # Then we get a result
    assert len(result) == 1
    assert "Heidelberg" in result[0].content
    assert "Heidelberg" in result[0].document_path.name
