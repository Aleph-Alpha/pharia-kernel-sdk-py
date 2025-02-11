from dataclasses import asdict

import pytest

from pharia_skill import CompletionParams
from pharia_skill.testing.dev.client import Client


@pytest.mark.kernel
def test_http_client_run(model: str):
    client = Client()
    params = CompletionParams(max_tokens=1)

    result = client.run(
        "complete",
        {
            "requests": [
                {
                    "model": model,
                    "prompt": "Say hello to Bob",
                    "params": asdict(params),
                },
            ],
        },
    )
    assert isinstance(result, list)
    assert result[0].get("text") is not None
