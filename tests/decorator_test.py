import pytest
from pydantic import BaseModel

from pharia_skill import CompletionParams, Csi, skill
from pharia_skill.decorator import Err
from pharia_skill.wit.exports.skill_handler import Error_InvalidInput


class Input(BaseModel):
    topic: str


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


def test_skill_with_too_many_arguments_raises_error():
    expected = "All arguments after the second argument must have defaults."
    with pytest.raises(AssertionError, match=expected):

        @skill  # type: ignore
        def foo(csi: Csi, input: Input, model: str):
            pass


def test_skill_with_default_arguments_does_not_raise():
    @skill  # type: ignore
    def foo(csi: Csi, input: Input, model: str = "llama"):
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


def test_skill_handler_can_list_models():
    @skill
    def foo(
        csi: Csi, input: Input, model: str = "llama-3.1", chat_gpt: str = "chat-gpt"
    ):
        pass

    handler = foo.__globals__["SkillHandler"]()
    assert handler.models() == ["llama-3.1", "chat-gpt"]
