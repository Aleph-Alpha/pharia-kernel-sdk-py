import pytest
from pydantic import BaseModel, RootModel

from pharia_skill import CompletionParams, Csi, skill
from pharia_skill.decorator import Err
from pharia_skill.wit.exports.skill_handler import Error_InvalidInput


class Input(BaseModel):
    topic: str


class Output(BaseModel):
    message: str


ListReturn = RootModel[list[str]]
StringReturn = RootModel[str]


@pytest.fixture(autouse=True)
def rm_skill_handler():
    if "SkillHandler" in globals():
        del globals()["SkillHandler"]


def test_skill_with_one_argument_raises_error():
    expected = "Skills must have exactly two arguments."
    with pytest.raises(AssertionError, match=expected):

        @skill  # type: ignore
        def foo(csi: Csi) -> None:
            pass


def test_skill_with_non_pydantic_model_raises_error():
    expected = "The second argument must be a Pydantic model"
    with pytest.raises(AssertionError, match=expected):

        @skill  # type: ignore
        def foo(csi: Csi, input: str) -> None:
            pass


def test_raise_error_if_two_skills_defined():
    @skill
    def foo(csi: Csi, input: Input) -> Output:
        return Output(message=input.topic)

    expected = "`@skill` can only be used once."
    with pytest.raises(AssertionError, match=expected):

        @skill
        def bar(csi: Csi, input: Input) -> Output:
            return Output(message=input.topic)


def test_skill_input_is_parsed_as_pydantic_model():
    @skill
    def foo(csi: Csi, input: Input) -> Output:
        return Output(message=input.topic)

    handler = foo.__globals__["SkillHandler"]()
    result = handler.run(b'{"topic": "llama"}')
    assert result == b'{"message":"llama"}'


def test_skill_without_output_type_raises_error():
    expected = "The function must have a return type annotation"
    with pytest.raises(AssertionError, match=expected):

        @skill  # type: ignore
        def foo(csi: Csi, input: Input):
            pass


def test_skill_output_is_serialized_as_json():
    @skill
    def foo(csi: Csi, input: Input) -> Output:
        return Output(message=input.topic)

    handler = foo.__globals__["SkillHandler"]()
    result = handler.run(b'{"topic": "llama"}')
    assert result == b'{"message":"llama"}'


def test_skill_raises_bad_input_error():
    @skill
    def foo(csi: Csi, input: Input) -> Output:
        return Output(message=input.topic)

    handler = foo.__globals__["SkillHandler"]()
    with pytest.raises(Err) as excinfo:
        handler.run(b'{"bad-input": 42}')

    assert isinstance(excinfo.value.value, Error_InvalidInput)


def test_skill_without_return_value_raises_error():
    expected = "The function must have a return type annotation"
    with pytest.raises(AssertionError, match=expected):

        @skill  # type: ignore
        def foo(csi: Csi, input: Input) -> None:
            pass


def test_skill_pydantic_output_schema():
    @skill
    def foo(csi: Csi, input: Input) -> Output:
        return Output(message=input.topic)

    handler = foo.__globals__["SkillHandler"]()
    assert handler.output_schema() == {
        "properties": {"message": {"title": "Message", "type": "string"}},
        "required": ["message"],
        "title": "Output",
        "type": "object",
    }


def test_skill_root_model_output_schema():
    """Pydantic supports returning `flat` types from skills."""

    @skill
    def foo(csi: Csi, input: Input) -> ListReturn:
        return ListReturn(["llama"])

    handler = foo.__globals__["SkillHandler"]()
    assert handler.output_schema() == {
        "title": "RootModel[list[str]]",
        "type": "array",
        "items": {"type": "string"},
    }

    result = handler.run(b'{"topic": "llama"}')
    assert result == b'["llama"]'


def test_skill_root_model_string_output_schema():
    @skill
    def foo(csi: Csi, input: Input) -> StringReturn:
        return StringReturn("llama")

    handler = foo.__globals__["SkillHandler"]()
    assert handler.output_schema() == {"title": "RootModel[str]", "type": "string"}

    result = handler.run(b'{"topic": "llama"}')
    assert result == b'"llama"'


def test_skill_pydantic_input_schema():
    @skill
    def foo(csi: Csi, input: Input) -> Output:
        return Output(message=input.topic)

    handler = foo.__globals__["SkillHandler"]()
    assert handler.input_schema() == {
        "properties": {"topic": {"title": "Topic", "type": "string"}},
        "required": ["topic"],
        "title": "Input",
        "type": "object",
    }


def test_skill_with_csi_call_raises_not_implemented():
    """Test call to the csi.complete call from bindings.

    Testing the csi injection in the `skill` decorator is tricky, as the WasiCsi
    is only used when the compiled skill is run in a Wasm environment. By asserting
    that a NonImplementedError is raised, we can be sure that the call to the bindings
    is executed correctly.
    """

    @skill
    def foo(csi: Csi, input: Input) -> Output:
        csi.complete("llama", "prompt", CompletionParams())
        return Output(message="llama")

    handler = foo.__globals__["SkillHandler"]()
    with pytest.raises(Err) as excinfo:
        handler.run(b'{"topic": "llama"}')

    assert "NotImplementedError" in excinfo.value.value.value
