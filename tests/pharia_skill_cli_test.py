from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from pharia_skill.cli import (
    IsMessageStream,
    IsSkill,
    NoHttpError,
    SkillType,
    run_componentize_py,
)
from pharia_skill.pharia_skill_cli import PhariaSkillCli


@pytest.mark.kernel
def test_download_pharia_skill():
    tempdir = TemporaryDirectory()
    dir = Path(tempdir.name)
    PhariaSkillCli.download_unix_tar(dir)
    assert (dir / "pharia-skill-cli").exists()


@pytest.mark.kernel
def test_download_pharia_skill_windows():
    tempdir = TemporaryDirectory()
    dir = Path(tempdir.name)
    PhariaSkillCli.download_windows_zip(dir)
    assert (dir / "pharia-skill-cli.exe").exists()


@pytest.mark.kernel
def test_pharia_skill_update_if_needed():
    PhariaSkillCli.update_if_needed()


def test_building_message_stream_skill_with_wrong_skill_type_raises():
    with pytest.raises(IsMessageStream):
        run_componentize_py(
            "tests.skills.streaming_haiku_chat",
            "haiku_stream.wasm",
            False,
            SkillType.SKILL,
        )


def test_building_skill_with_wrong_skill_type_raises():
    with pytest.raises(IsSkill):
        run_componentize_py(
            "tests.skills.haiku",
            "haiku.wasm",
            False,
            SkillType.MESSAGE_STREAM_SKILL,
        )


def test_building_skill_which_imports_requests_raises():
    with pytest.raises(NoHttpError):
        run_componentize_py(
            "tests.skills.http_haiku",
            "http_haiku.wasm",
            False,
            SkillType.SKILL,
        )
