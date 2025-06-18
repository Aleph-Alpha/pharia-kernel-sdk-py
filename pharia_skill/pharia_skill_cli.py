import logging
import os
import subprocess
import sys
from typing import NamedTuple

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class Registry(NamedTuple):
    """Where and How do I publish my skill?"""

    user: str
    token: str
    registry: str
    repository: str

    @classmethod
    def from_env(cls) -> "Registry":
        load_dotenv()
        return cls(
            user=os.environ["SKILL_REGISTRY_USER"],
            token=os.environ["SKILL_REGISTRY_TOKEN"],
            registry=os.environ["SKILL_REGISTRY"],
            repository=os.environ["SKILL_REPOSITORY"],
        )


def cli_publish(skill: str, name: str | None, tag: str, registry: Registry) -> None:
    """Publish a skill to an OCI registry.

    Takes a path to a Wasm component, wrap it in an OCI image and publish it to an OCI
    registry under the `latest` tag. This does not fully deploy the skill, as an older
    version might still be cached in the Kernel.
    """
    # add file extension
    if not skill.endswith(".wasm"):
        skill += ".wasm"

    # allow relative paths
    if not skill.startswith(("/", "./")):
        skill = f"./{skill}"

    if not os.path.exists(skill):
        logger.error(f"No such file: {skill}")
        sys.exit(1)

    command = [
        "pharia-skill-cli",
        "publish",
        "-R",
        registry.registry,
        "-r",
        registry.repository,
        "-u",
        registry.user,
        "-p",
        registry.token,
        *(["-n", name] if name else []),
        "-t",
        tag,
        skill,
    ]

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError:
        sys.exit(1)
