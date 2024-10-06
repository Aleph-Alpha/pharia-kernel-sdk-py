import argparse
import importlib
import inspect
import logging
import os
import subprocess

import requests
import uvicorn
from dotenv import load_dotenv

from .decorator import Skill
from .testing.server import build_app

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


def invalidate_cache(skill: str):
    try:
        kernel_address = os.environ["PHARIA_KERNEL_ADDRESS"]
        token = os.environ["AA_API_TOKEN"]
        namespace = os.environ["SKILL_NAMESPACE"]
    except KeyError as e:
        logger.error(f"Environment variable {e} is not set.")
        return

    url = f"{kernel_address}/cached_skills/{namespace}%2f{skill}"
    headers = {"Authorization": f"Bearer {token}"}
    logger.info("Invalidating cache...")
    response = requests.delete(url, headers=headers)
    if response.status_code not in (200, 204):
        raise Exception(f"{response.status_code}: {response.text}")
    logger.info(response.json())


def find_skill_in_module(module: str) -> Skill | None:
    """Find a function decorated with @skill in a given module."""
    imported_module = importlib.import_module(module)

    for _name, func in inspect.getmembers(imported_module, inspect.isfunction):
        if getattr(func, "_is_skill", False):
            return func

    return None


def run_server(module: str, host: str, port: int):
    """Run a skill server that makes a skill available via HTTP."""
    if (skill := find_skill_in_module(module)) is None:
        raise Exception("No function decorated with @skill found in the module")

    app = build_app(skill)
    uvicorn.run(app, host=host, port=port)


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

    up_parser = subparsers.add_parser(
        "up",
        help="Make a skill available via HTTP. Ignores provided namespaces when executing the skill.",
    )
    up_parser.add_argument("skill", help="Python module of the skill to run")
    up_parser.add_argument(
        "--host", help="Host where to run the HTTP server", default="127.0.0.1"
    )
    up_parser.add_argument(
        "--port", help="Port where to run the HTTP server", type=int, default=8000
    )

    args = parser.parse_args()

    try:
        if args.command == "build":
            setup_wasi_deps()
            run_componentize_py(args.skill)
        elif args.command == "publish":
            publish(args.skill)
            invalidate_cache(args.skill)
        elif args.command == "up":
            run_server(args.skill, args.host, args.port)
        else:
            parser.print_help()
    except subprocess.CalledProcessError as e:
        logger.error(f"Command '{e.cmd}' returned non-zero exit status {e.returncode}.")
        logger.error(f"Error message: {e.stderr}")


if __name__ == "__main__":
    main()
