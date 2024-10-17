import pytest

from pharia_skill.csi import (
    ChunkParams,
    CompletionParams,
    CompletionRequest,
    IndexPath,
    Language,
)
from pharia_skill.testing import DevCsi


@pytest.fixture(scope="module")
def csi() -> DevCsi:
    return DevCsi()


@pytest.mark.kernel
def test_complete(csi: DevCsi):
    params = CompletionParams(max_tokens=64)
    result = csi.complete("llama-3.1-8b-instruct", "Say hello to Bob", params)
    assert "Bob" in result.text


@pytest.mark.kernel
def test_chunk(csi: DevCsi):
    text = "A very very very long text that can be chunked."
    params = ChunkParams(model="llama-3.1-8b-instruct", max_tokens=1)
    result = csi.chunk(text, params)
    assert len(result) == 13


@pytest.mark.kernel
def test_select_language(csi: DevCsi):
    text = "Ich spreche Deutsch nur ein bisschen."
    languages = [Language.ENG, Language.DEU]
    result = csi.select_language(text, languages)
    assert result == Language.DEU


@pytest.mark.kernel
def test_complete_all(csi: DevCsi):
    params = CompletionParams(max_tokens=64)
    request_1 = CompletionRequest("llama-3.1-8b-instruct", "Say hello to Alice", params)
    request_2 = CompletionRequest("llama-3.1-8b-instruct", "Say hello to Bob", params)
    result = csi.complete_all([request_1, request_2])
    assert len(result) == 2
    assert "Alice" in result[0].text
    assert "Bob" in result[1].text


@pytest.mark.kernel
def testsearch(csi: DevCsi):
    # Given an existing index
    index_path = IndexPath("f13", "wikipedia-de", "luminous-base-asymmetric-64")
    query = "What is the population of Heidelberg?"

    # When searching
    result = csi.search(index_path, query)

    # Then we get a result
    assert len(result) == 1
    assert "Heidelberg" in result[0].content
    assert "Heidelberg" in result[0].document_path.name
