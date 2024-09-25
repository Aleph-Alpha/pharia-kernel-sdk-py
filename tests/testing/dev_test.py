from pharia_skill.csi import (
    ChunkParams,
    CompletionParams,
    CompletionRequest,
    Language,
)
from pharia_skill.testing import _DevCsi


def test_complete():
    params = CompletionParams(max_tokens=64)
    csi = _DevCsi()
    result = csi.complete("llama-3.1-8b-instruct", "Say hello to Bob", params)
    assert "Bob" in result.text


def test_chunk():
    text = "A very very very long text that can be chunked."
    params = ChunkParams(model="llama-3.1-8b-instruct", max_tokens=1)
    csi = _DevCsi()
    result = csi.chunk(text, params)
    assert len(result) == 13


def test_select_language():
    text = "Ich spreche Deutsch nur ein bisschen."
    languages = [Language.ENG, Language.DEU]
    csi = _DevCsi()
    result = csi.select_language(text, languages)
    assert result == Language.DEU


def test_complete_all():
    params = CompletionParams(max_tokens=64)
    request_1 = CompletionRequest(
        "llama-3.1-8b-instruct", "Say hello to Alice", params
    )
    request_2 = CompletionRequest(
        "llama-3.1-8b-instruct", "Say hello to Bob", params
    )
    csi = _DevCsi()
    result = csi.complete_all([request_1, request_2])
    assert len(result) == 2
    assert "Alice" in result[0].text
    assert "Bob" in result[1].text
