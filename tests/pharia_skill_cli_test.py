import os

import pytest

from pharia_skill.cli import run_componentize_py, setup_wasi_deps
from pharia_skill.pharia_skill_cli import PhariaSkillCli


@pytest.fixture
def build_skill() -> str:
    """Ensure a built skill exists."""
    if not os.path.exists("haiku.wasm"):
        setup_wasi_deps()
        run_componentize_py("examples.haiku")
    return "haiku.wasm"


def test_download_pharia_skill():
    response = PhariaSkillCli.download_pharia_skill()
    assert response is not None


def test_pharia_skill_update_if_needed():
    PhariaSkillCli.update_if_needed()


def test_publish_skill(build_skill: str):
    cli = PhariaSkillCli()
    cli.publish(build_skill)
