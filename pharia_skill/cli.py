import logging
import os
import subprocess

import typer
from typing_extensions import Annotated

from .pharia_skill_cli import PhariaSkillCli

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


def setup_wasi_deps() -> None:
    """Download the Pydantic WASI wheels if they are not already present."""
    PYDANTIC_CORE_VERSION = "2.27.2"
    WASI_DEPS_PATH = "wasi_deps"
    if os.path.exists(WASI_DEPS_PATH):
        if not os.path.exists(
            f"{WASI_DEPS_PATH}/pydantic_core-{PYDANTIC_CORE_VERSION}.dist-info"
        ):
            logger.info("Deleting outdated Pydantic Wasi wheels...")
            subprocess.run(["rm", "-rf", WASI_DEPS_PATH])

    if not os.path.exists(WASI_DEPS_PATH):
        logger.info("Downloading Pydantic Wasi wheels...")
        subprocess.run(
            [
                "pip3",
                "install",
                "--target",
                WASI_DEPS_PATH,
                "--only-binary",
                ":all:",
                "--platform",
                "any",
                "--platform",
                "wasi_0_0_0_wasm32",
                "--python-version",
                "3.12",
                f"https://github.com/benbrandt/wasi-wheels/releases/download/pydantic-core/v{PYDANTIC_CORE_VERSION}/pydantic_core-{PYDANTIC_CORE_VERSION}-cp312-cp312-wasi_0_0_0_wasm32.whl",
            ],
            check=True,
        )


def run_componentize_py(skill_module: str, unstable: bool) -> None:
    """Build the skill to a WASM component using componentize-py.

    The call to componentize-py targets the `skill` wit world and adds the downloaded
    Pydantic WASI wheels to the Python path.
    """
    if "/" in skill_module or skill_module.endswith(".py"):
        logger.error(
            f"argument must be fully qualified python module name, not {skill_module}"
        )
        return
    output_file = f"./{skill_module.split('.')[-1]}.wasm"
    args = ["--all-features"] if unstable else []
    command = [
        "componentize-py",
        *args,
        "-w",
        "skill",
        "componentize",
        skill_module,
        "-o",
        output_file,
        "-p",
        ".",
        "-p",
        "wasi_deps",
    ]
    logger.info(f"Building WASM component {output_file} from {skill_module} ...")
    subprocess.run(command, check=True)


app = typer.Typer()


@app.callback()
def callback() -> None:
    """
    Pharia Skill CLI Tool.
    """


@app.command()
def build(
    skill: Annotated[str, typer.Argument(help="Python module of the skill to build")],
    unstable: Annotated[
        bool,
        typer.Option(
            help="Enable unstable features for testing. Don't try this at home."
        ),
    ] = False,
) -> None:
    """
    Build a skill.
    """
    setup_wasi_deps()
    run_componentize_py(skill, unstable)


@app.command()
def publish(
    skill: Annotated[
        str,
        typer.Argument(
            help="Path to the component to publish without the .wasm extension"
        ),
    ],
    tag: Annotated[
        str, typer.Option(help='default to "latest" if not provided')
    ] = "latest",
) -> None:
    """
    Publish a skill.
    """
    cli = PhariaSkillCli()
    cli.publish(skill, tag)


if __name__ == "__main__":
    app()
