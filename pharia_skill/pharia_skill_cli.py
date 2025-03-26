import io
import logging
import os
import platform
import subprocess
import tarfile
import zipfile
from pathlib import Path
from typing import NamedTuple

import requests
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
        return cls(
            user=os.environ["SKILL_REGISTRY_USER"],
            token=os.environ["SKILL_REGISTRY_TOKEN"],
            registry=os.environ["SKILL_REGISTRY"],
            repository=os.environ["SKILL_REPOSITORY"],
        )


class PhariaSkillCli:
    """The `pharia-skill-cli` rust crate is used for publishing skills.

    This class manages the installation of the `pharia-skill-cli` binary and provides
    an interface to its commands.

    We make sure the `pharia-skill-cli` binary is up to date before allowing users to invoke commands.
    """

    # Expected version of the `pharia-skill-cli` binary
    PHARIA_SKILL_CLI_VERSION = "0.4.4"

    PHARIA_SKILL_CLI_PATH = (
        "bin/pharia-skill-cli"
        if "Windows" not in platform.system()
        else ".\\bin\\pharia-skill-cli.exe"
    )

    def __init__(self) -> None:
        load_dotenv()
        self.update_if_needed()

    @classmethod
    def update_if_needed(cls) -> None:
        if not os.path.exists(cls.PHARIA_SKILL_CLI_PATH) or not cls.is_up_to_date():
            cls.download_pharia_skill()
            assert cls.is_up_to_date()

    @classmethod
    def is_up_to_date(cls) -> bool:
        return cls.pharia_skill_version() == cls.PHARIA_SKILL_CLI_VERSION

    @classmethod
    def pharia_skill_version(cls) -> str | None:
        """Version of the currently installed `pharia-skill-cli` binary."""
        result = subprocess.run(
            [cls.PHARIA_SKILL_CLI_PATH, "--version"],
            stdout=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0:
            return None

        # pharia-skill-cli version is in the format "pharia-skill-cli 0.1.0"
        return result.stdout.strip().split(" ")[-1]

    @classmethod
    def architecture(cls) -> str:
        match platform.system():
            case "Darwin":
                if platform.machine() == "arm64":
                    return "aarch64-apple-darwin"
                else:
                    return "x86_64-apple-darwin"
            case "Linux":
                return "x86_64-unknown-linux-gnu"
            case "Windows":
                return "x86_64-pc-windows-msvc"
            case _:
                raise Exception(f"Unsupported operating system: {platform.system()}")

    @classmethod
    def download_pharia_skill(cls) -> None:
        logger.info(
            f"Downloading pharia-skill-cli version {cls.PHARIA_SKILL_CLI_VERSION} for {cls.architecture()}"
        )
        os.makedirs("bin", exist_ok=True)
        for file in os.listdir("bin"):
            os.remove(os.path.join("bin", file))

        match cls.architecture():
            case (
                "aarch64-apple-darwin"
                | "x86_64-apple-darwin"
                | "x86_64-unknown-linux-gnu"
            ):
                cls.download_unix_tar(Path("bin"))
            case "x86_64-pc-windows-msvc":
                cls.download_windows_zip(Path("bin"))
            case _:
                raise Exception(f"Unsupported architecture: {cls.architecture()}")

        logger.info("Pharia skill CLI installed successfully.")

    @classmethod
    def download_unix_tar(cls, dir: Path) -> None:
        filename = f"pharia-skill-cli-{cls.architecture()}"
        url = f"https://github.com/Aleph-Alpha/pharia-skill-cli/releases/download/v{cls.PHARIA_SKILL_CLI_VERSION}/{filename}.tar.xz"
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"{response.status_code}: {response.text}")

        file = tarfile.open(fileobj=io.BytesIO(response.content)).extractfile(
            filename + "/pharia-skill-cli"
        )
        assert file, "pharia-skill-cli not found in archive"
        with open(dir / "pharia-skill-cli", "wb") as f:
            f.write(file.read())
        subprocess.run(["chmod", "+x", dir / "pharia-skill-cli"], check=True)

    @classmethod
    def download_windows_zip(cls, dir: Path) -> None:
        url = f"https://github.com/Aleph-Alpha/pharia-skill-cli/releases/download/v{cls.PHARIA_SKILL_CLI_VERSION}/pharia-skill-cli-x86_64-pc-windows-msvc.zip"
        print(url)
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"{response.status_code}: {response.text}")

        zipfile.ZipFile(io.BytesIO(response.content)).extract(
            "pharia-skill-cli.exe", path=dir
        )

    def publish(
        self, skill: str, name: str | None, tag: str, registry: Registry
    ) -> None:
        """Publish a skill to an OCI registry.

        Takes a path to a WASM component, wrap it in an OCI image and publish it to an OCI
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
            return
        command = [
            self.PHARIA_SKILL_CLI_PATH,
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
        subprocess.run(command, check=True)
