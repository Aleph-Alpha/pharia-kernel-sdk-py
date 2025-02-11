import json
from typing import Any

import pytest


@pytest.fixture(scope="module")
def model() -> str:
    return "llama-3.1-8b-instruct"


def dumps(value: Any) -> str:
    """Dump a value to JSON without any whitespace.

    This matches the representation we get from pydantic when calling `model_dump_json()`.
    See https://github.com/pydantic/pydantic/issues/6606
    """
    return json.dumps(value, separators=(",", ":"))
