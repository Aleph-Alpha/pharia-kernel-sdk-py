import argparse
import logging
import os
import subprocess

from dotenv import load_dotenv

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
    subprocess.run(command, check=True)


def image_exists(image_name: str) -> bool:
    """Check if a given podman image exists locally."""
    result = subprocess.run(
        ["podman", "images", "--format", "{{.Repository}}:{{.Tag}}"],
        stdout=subprocess.PIPE,
        text=True,
    )

    return image_name in result.stdout


def publish(skill: str):
    """Publish a skill to an OCI registry.

    Takes a path to a WASM component, wrap it in an OCI image and publish it to an OCI
    registry under the `latest` tag. This does not fully deploy the skill, as an older
    version might still be cached in the Kernel.
    """
    try:
        jfrog_user = os.environ["JFROG_USER"]
        jfrog_password = os.environ["JFROG_PASSWORD"]
        gitlab_token = os.environ["GITLAB_TOKEN"]
        skill_registry = os.environ["SKILL_REGISTRY"]
        skill_repository = os.environ["SKILL_REPOSITORY"]
    except KeyError as e:
        logger.error(f"Environment variable {e} is not set.")
        return

    image = "alephalpha.jfrog.io/pharia-kernel-images/pharia-skill:latest"

    if not image_exists(image):
        logger.info("Pulling pharia-skill image...")

        subprocess.run(
            [
                "podman",
                "login",
                "alephalpha.jfrog.io/pharia-kernel-images",
                "-u",
                jfrog_user,
                "-p",
                jfrog_password,
            ],
            check=True,
        )

        subprocess.run(["podman", "pull", image], check=True)
        subprocess.run(["podman", "tag", image, "pharia-skill"], check=True)

    # add file extension
    if not skill.endswith(".wasm"):
        skill += ".wasm"

    # allow relative paths
    if not skill.startswith(("/", "./")):
        skill = f"./{skill}"

    container_path = "/" + skill.split("/")[-1]
    volume = f"{skill}:{container_path}"
    command = [
        "podman",
        "run",
        "-v",
        volume,
        "pharia-skill",
        "publish",
        "-R",
        skill_registry,
        "-r",
        skill_repository,
        "-u",
        "DUMMY_USER_NAME",
        "-p",
        gitlab_token,
        "-t",
        "latest",
        container_path,
    ]
    subprocess.run(command, check=True)
    logger.info("Skill published successfully.")


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
            publish(args.skill)
        else:
            parser.print_help()
    except subprocess.CalledProcessError as e:
        logger.error(f"Command '{e.cmd}' returned non-zero exit status {e.returncode}.")
        logger.error(f"Error message: {e.stderr}")


if __name__ == "__main__":
    main()
