from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

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
