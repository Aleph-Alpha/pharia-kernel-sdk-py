import pytest

from pharia_skill.testing import StubCsi

from .failing import Input, failing


def test_skill_raises():
    input = Input(root="Oat milk")
    csi = StubCsi()
    with pytest.raises(ValueError):
        failing(csi, input)
