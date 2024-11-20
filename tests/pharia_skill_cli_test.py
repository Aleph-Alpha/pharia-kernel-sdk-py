import pytest

from pharia_skill.pharia_skill_cli import PhariaSkillCli


@pytest.mark.kernel
def test_download_pharia_skill():
    response = PhariaSkillCli.download_pharia_skill()
    assert response is not None


@pytest.mark.kernel
def test_pharia_skill_update_if_needed():
    PhariaSkillCli.update_if_needed()
