import pytest
from pydantic import BaseModel

from pharia_skill import CompletionParams, Csi, skill
from pharia_skill.decorator import Err, as_json_str
from pharia_skill.wit.exports.skill_handler import Error_InvalidInput


class Input(BaseModel):
    topic: str


class Output(BaseModel):
    message: str


@pytest.fixture(autouse=True)
def rm_skill_handler():
    if "SkillHandler" in globals():
        del globals()["SkillHandler"]


def test_skill_with_one_argument_raises_error():
    expected = "Skills must have exactly two arguments."
    with pytest.raises(AssertionError, match=expected):

        @skill  # type: ignore
        def foo(csi: Csi):
            pass


def test_skill_with_non_pydantic_model_raises_error():
    expected = "The second argument must be a Pydantic model"
    with pytest.raises(AssertionError, match=expected):

        @skill  # type: ignore
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
    def foo(csi: Csi, input: Input) -> str:
        return input.topic

    handler = foo.__globals__["SkillHandler"]()
    result = handler.run(b'{"topic": "llama"}')
    assert result == b'"llama"'


def test_skill_output_is_serialized_as_json():
    @skill
    def foo(csi: Csi, input: Input) -> Output:
        return Output(message=input.topic)

    handler = foo.__globals__["SkillHandler"]()
    result = handler.run(b'{"topic": "llama"}')
    assert result == b'{"message":"llama"}'


def test_skill_raises_bad_input_error():
    @skill
    def foo(csi: Csi, input: Input) -> str:
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


def test_skill_with_csi_call_raises_not_implemented():
    """Test call to the csi.complete call from bindings.

    Testing the csi injection in the `skill` decorator is tricky, as the WasiCsi
    is only used when the compiled skill is run in a Wasm environment. By asserting
    that a NonImplementedError is raised, we can be sure that the call to the bindings
    is executed correctly.
    """

    @skill
    def foo(csi: Csi, input: Input):
        csi.complete("llama", "prompt", CompletionParams())

    handler = foo.__globals__["SkillHandler"]()
    with pytest.raises(Err) as excinfo:
        handler.run(b'{"topic": "llama"}')

    assert "NotImplementedError" in excinfo.value.value.value


def test_as_json_str():
    assert as_json_str(None) == "null"
    assert as_json_str("llama") == '"llama"'
    assert as_json_str(Output(message="llama")) == '{"message":"llama"}'
