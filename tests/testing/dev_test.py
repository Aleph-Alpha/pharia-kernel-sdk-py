from pharia_skill.csi import CompletionParams
from pharia_skill.testing import _DevCsi


def test_complete():
    params = CompletionParams(max_tokens=128)
    result = _DevCsi.complete("llama-3.1-8b-instruct", "Say hello to Bob", params)
    assert "Bob" in result.text
