from pharia_skill.testing import StubCsi
from pharia_skill.wit.imports.csi import CompletionParams, CompletionRequest


def test_complete_all():
    # given
    params = CompletionParams(None, None, None, None, [])
    request_1 = CompletionRequest("model_1", "prompt_1", params)
    request_2 = CompletionRequest("model_2", "prompt_2", params)

    # when
    completions = StubCsi.complete_all([request_1, request_2])

    # then
    assert completions[0].text == "prompt_1"
    assert completions[1].text == "prompt_2"
