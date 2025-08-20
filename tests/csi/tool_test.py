import pytest
from pydantic import ValidationError

from pharia_skill.csi.inference.tool import InvokeRequest


def test_validation_of_invoke_request():
    InvokeRequest(name="add", arguments={"a": 1, "b": 2})


def test_nested_json_value():
    InvokeRequest(name="add", arguments={"a": [1, 2], "b": {"c": 3}})


def test_validation_error_for_invalid_json_value():
    # Given a class that is not JSON serializable
    class MyClass:
        pass

    # Then an error is raised when we try to put it in the arguments
    with pytest.raises(ValidationError):
        InvokeRequest(name="add", arguments={"a": 1, "b": {"c": MyClass()}})  # type: ignore
