from pharia_skill import CompletionParams, CompletionRequest
from pharia_skill.testing import StubCsi


def test_complete_all():
    # given
    params = CompletionParams()
    request_1 = CompletionRequest(model="model_1", prompt="prompt_1", params=params)
    request_2 = CompletionRequest(model="model_2", prompt="prompt_2", params=params)

    # when
    csi = StubCsi()
    completions = csi.complete_all([request_1, request_2])

    # then
    assert completions[0].text == "prompt_1"
    assert completions[1].text == "prompt_2"
