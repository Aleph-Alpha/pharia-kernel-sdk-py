from pharia_skill.testing import DevCsi

from .tool_call import Input, Output, compute


def test_compute():
    input = Input(root=2)
    result = compute(DevCsi(namespace="test-beta"), input)
    assert isinstance(result, Output)
    assert result.root == 42
