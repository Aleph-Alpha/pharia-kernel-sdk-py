from pharia_skill import CompletionParams, CompletionRequest
from pharia_skill.testing import StubCsi


def test_complete():
    # given
    params = CompletionParams()
    request_1 = CompletionRequest("model_1", "prompt_1", params)
    request_2 = CompletionRequest("model_2", "prompt_2", params)

    # when
    csi = StubCsi()
    completions = csi.complete_concurrent([request_1, request_2])

    # then
    assert completions[0].text == "prompt_1"
    assert completions[1].text == "prompt_2"
