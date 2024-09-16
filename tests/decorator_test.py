import pytest
from pharia_skill import skill

def test_raise_error_if_two_skills_defined():
    @skill
    def foo():
        pass

    with pytest.raises(AssertionError):
        @skill
        def bar():
            pass
