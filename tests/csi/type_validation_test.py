import pytest
from pydantic import ValidationError

from pharia_skill.csi.inference import CompletionParams


def test_exposed_classes_validate_types():
    with pytest.raises(ValidationError):
        CompletionParams(max_tokens="max_tokens")  # type: ignore
