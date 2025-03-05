import os
from typing import NamedTuple

import oci_publish
from dotenv import load_dotenv


class Registry(NamedTuple):
    """Where and how do I publish my skill?"""

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

    def publish(self, skill_path: str, name: str, tag: str) -> None:
        oci_publish.publish(
            skill_path,
            self.registry,
            self.repository,
            name,
            tag,
            self.user,
            self.token,
        )
