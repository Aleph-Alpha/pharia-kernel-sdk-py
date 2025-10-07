import pytest

from pharia_skill.cli import (
    IsMessageStream,
    IsSkill,
    NoHttpError,
    SkillType,
    run_componentize_py,
    setup_wasi_deps,
)


@pytest.fixture(autouse=True)
def wasi_wheels_installed():
    setup_wasi_deps()


def test_building_message_stream_skill_with_wrong_skill_type_raises():
    with pytest.raises(IsMessageStream):
        run_componentize_py(
            "tests.skills.streaming_haiku_chat",
            "haiku_stream.wasm",
            True,
            SkillType.SKILL,
            [],
        )


def test_building_skill_with_wrong_skill_type_raises():
    with pytest.raises(IsSkill):
        run_componentize_py(
            "tests.skills.haiku",
            "haiku.wasm",
            True,
            SkillType.MESSAGE_STREAM_SKILL,
            [],
        )


def test_building_skill_which_imports_requests_raises():
    with pytest.raises(NoHttpError):
        run_componentize_py(
            "tests.skills.http_haiku",
            "http_haiku.wasm",
            True,
            SkillType.SKILL,
            [],
        )
