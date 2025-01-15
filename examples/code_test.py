from pharia_skill.testing import DevCsi

from .code import Input, code


def test_haiku():
    input = Input(question="Run code to compute the first ten prime numbers")
    result = code(DevCsi(), input)
    assert result.executed_code is not None
    assert result.code_result is not None
