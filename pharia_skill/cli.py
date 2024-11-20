import argparse
import logging
import os
import subprocess

from dotenv import load_dotenv

from .pharia_skill_cli import PhariaSkillCli

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


def setup_wasi_deps():
    """Download the Pydantic WASI wheels if they are not already present."""
    if not os.path.exists("wasi_deps"):
        logger.info("Downloading Pydantic Wasi wheels...")
        os.makedirs("wasi_deps")
        os.chdir("wasi_deps")

        subprocess.run(
            [
                "curl",
                "-OL",
                "https://github.com/dicej/wasi-wheels/releases/download/latest/pydantic_core-wasi.tar.gz",
            ],
            check=True,
        )

        subprocess.run(["tar", "xf", "pydantic_core-wasi.tar.gz"], check=True)
        subprocess.run(["rm", "pydantic_core-wasi.tar.gz"], check=True)
        os.chdir("..")


def run_componentize_py(skill_module: str):
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
    command = [
        "componentize-py",
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


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Pharia Skill CLI Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    build_parser = subparsers.add_parser("build", help="Build a skill")
    build_parser.add_argument("skill", help="Python module of the skill to build")

    publish_parser = subparsers.add_parser("publish", help="Publish a skill")
    publish_parser.add_argument(
        "skill", help="Path to the component to publish without the .wasm extension"
    )

    args = parser.parse_args()

    try:
        if args.command == "build":
            setup_wasi_deps()
            run_componentize_py(args.skill)
        elif args.command == "publish":
            cli = PhariaSkillCli()
            cli.publish(args.skill)
        else:
            parser.print_help()
    except subprocess.CalledProcessError as e:
        logger.error(f"Command '{e.cmd}' returned non-zero exit status {e.returncode}.")
        logger.error(f"Error message: {e.stderr}")
        exit(e.returncode)


if __name__ == "__main__":
    main()
