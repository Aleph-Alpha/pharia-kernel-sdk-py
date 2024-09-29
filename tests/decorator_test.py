import pytest
from pydantic import BaseModel

from pharia_skill import Csi, skill
from pharia_skill.wit.exports.skill_handler import Error_InvalidInput
from pharia_skill.wit.types import Err


class Input(BaseModel):
    topic: str


@pytest.fixture(autouse=True)
def rm_skill_handler():
    if "SkillHandler" in globals():
        del globals()["SkillHandler"]


def test_skill_with_one_argument_raises_error():
    expected = "Skills must have exactly two arguments."
    with pytest.raises(AssertionError, match=expected):

        @skill
        def foo(csi: Csi):
            pass


def test_skill_with_non_pydantic_model_raises_error():
    expected = "The second argument must be a Pydantic model"
    with pytest.raises(AssertionError, match=expected):

        @skill
        def foo(csi: Csi, input: str):
            pass


def test_raise_error_if_two_skills_defined():
    @skill
    def foo(csi: Csi, input: Input):
        pass

    expected = "`@skill` can only be used once."
    with pytest.raises(AssertionError, match=expected):

        @skill
        def bar(csi: Csi, input: Input):
            pass


def test_skill_input_is_parsed_as_pydantic_model():
    @skill
    def foo(csi: Csi, input: Input):
        return input.topic

    handler = foo.__globals__["SkillHandler"]()
    result = handler.run(b'{"topic": "llama"}')
    assert result == b'"llama"'


def test_skill_raises_bad_input_error():
    @skill
    def foo(csi: Csi, input: Input):
        return input.topic

    handler = foo.__globals__["SkillHandler"]()
    with pytest.raises(Err) as excinfo:
        handler.run(b'{"bad-input": 42}')

    assert isinstance(excinfo.value.value, Error_InvalidInput)


def test_skill_without_return_value():
    @skill
    def foo(csi: Csi, input: Input):
        pass

    handler = foo.__globals__["SkillHandler"]()
    result = handler.run(b'{"topic": "llama"}')
    assert result == b"null"
