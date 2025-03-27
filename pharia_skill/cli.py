import importlib
import inspect
import logging
import os
import subprocess
import time
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.prompt import Confirm, Prompt
from typing_extensions import Annotated

from .pharia_skill_cli import PhariaSkillCli, Registry

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)
console = Console()


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
                "--index-url",
                "https://benbrandt.github.io/wasi-wheels/",
                "--extra-index-url",
                "https://pypi.org/simple",
                f"pydantic-core=={PYDANTIC_CORE_VERSION}",
            ],
            check=True,
        )


class BuildError(Exception):
    def __init__(self, message: str):
        self.message = message


class ModuleError(Exception):
    pass


def inspect_wit_world(module_path: str) -> str:
    """Determine the world that a Skill should be build against.

    The SDK supports multiple wit worlds (e.g. `skill` and `message-stream-skill`).
    Each decorator targets a particular world.

    This function inspects a module, looking for one of the exported classes
    to determine which world the Skill should be build against.
    """
    if contains_class(module_path, "SkillHandler"):
        return "skill"
    elif contains_class(module_path, "MessageStream"):
        return "message-stream-skill"
    else:
        raise ValueError(
            f"Unable to find a Skill in {module_path}. "
            "Did you add the @skill or @message_stream decorator to the Skill function?"
        )


def contains_class(module_path: str, class_name: str) -> bool:
    """Check if a class named `class_name` exists in the given module."""
    module = importlib.import_module(module_path)
    return any(
        name == class_name and inspect.isclass(value)
        for name, value in vars(module).items()
    )


def run_componentize_py(skill_module: str, output_file: str, unstable: bool) -> str:
    """Build the skill to a WASM component using componentize-py.

    The call to componentize-py targets the `skill` wit world and adds the downloaded
    Pydantic WASI wheels to the Python path.

    Returns:
        str: The path to the generated WASM file.
    """
    setup_wasi_deps()
    args = ["--all-features"] if unstable else []
    world = inspect_wit_world(skill_module)
    command = [
        "componentize-py",
        *args,
        "-w",
        world,
        "componentize",
        skill_module,
        "-o",
        output_file,
        "-p",
        ".",
        "-p",
        "wasi_deps",
    ]

    try:
        subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        raise BuildError(e.stderr)

    return output_file


def display_publish_suggestion(wasm_file: str) -> None:
    """Display a colorful suggestion to publish the skill.

    Args:
        wasm_file: Path to the generated WASM file.
    """
    wasm_filename = wasm_file.lstrip("./")
    publish_command = f"pharia-skill publish {wasm_filename} --tag [TAG] --name [NAME]"

    console.print(
        Panel.fit(
            f"[bold]Skill:[/bold] [cyan]{wasm_filename}[/cyan]\n\n"
            f"[yellow]To publish, run:[/yellow]\n"
            f"[cyan]{publish_command}[/cyan]",
            title="[bold green]Build Successful[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
    )


def publish_skill(skill_path: str, name: Optional[str], tag: str) -> None:
    """Publish a skill with progress indicator and success message.

    Args:
        skill_path: Path to the WASM file to publish.
        name: Name to publish the skill as, or None to use the filename.
        tag: Tag to publish the skill with.
    """
    if not skill_path.endswith(".wasm"):
        skill_path += ".wasm"

    display_name = name if name else skill_path.replace(".wasm", "")

    cli = PhariaSkillCli()

    try:
        registry = Registry.from_env()
    except KeyError as e:
        console.print(
            Panel(
                f"The environment variable [yellow]{e}[/yellow] is not set.",
                title="[bold red]Error[/bold red]",
                border_style="red",
                padding=(1, 1),
            )
        )
        raise typer.Exit(code=1)

    start_time = time.time()
    with Progress(
        SpinnerColumn(),
        TextColumn(f"Publishing [cyan]{display_name}[/cyan]:[cyan]{tag}[/cyan]..."),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("", total=None)
        cli.publish(skill_path, name, tag, registry)
        progress.update(task, completed=True)

    console.print(
        Panel.fit(
            f"[bold]Skill:[/bold] [cyan]{display_name}[/cyan]\n"
            f"[bold]Tag:[/bold] [cyan]{tag}[/cyan]\n"
            f"[bold]Registry:[/bold] [cyan]{registry.registry}/{registry.repository}[/cyan]\n\n"
            f"Published in [yellow]{time.time() - start_time:.2f}[/yellow] seconds",
            title="[bold green]Publish Successful[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
    )


def prompt_for_publish(wasm_file: str) -> None:
    """Prompt the user to publish the skill.

    Args:
        wasm_file: Path to the generated WASM file.
    """
    wasm_filename = wasm_file.lstrip("./")

    # Ask if the user wants to publish now with a more engaging prompt
    if Confirm.ask(
        "\n[bold yellow]Would you like to publish this skill now?[/bold yellow]",
        default=True,
        console=console,
    ):
        tag = Prompt.ask(
            "[bold cyan]Enter tag[/bold cyan]",
            default="latest",
            show_default=True,
            console=console,
        )

        name_default = wasm_filename.replace(".wasm", "")
        name = Prompt.ask(
            "[bold cyan]Enter name[/bold cyan]",
            default=name_default,
            show_default=True,
            console=console,
        )

        # Publish the skill
        publish_skill(wasm_filename, name, tag)


app = typer.Typer(rich_markup_mode="rich")


@app.callback()
def callback() -> None:
    """
    [bold green]Pharia Skill CLI Tool[/bold green].

    A tool for building and publishing Pharia Skills.
    """


@app.command()
def build(
    skill: Annotated[
        str,
        typer.Argument(help="Python module of the skill to build", show_default=False),
    ],
    unstable: Annotated[
        bool,
        typer.Option(
            help="Enable unstable features for testing. Don't try this at home."
        ),
    ] = False,
    interactive: Annotated[
        bool,
        typer.Option(
            help="Prompt for publishing after building.",
            show_default=True,
        ),
    ] = True,
) -> None:
    """
    [bold blue]Build[/bold blue] a skill.

    Compiles a Python module into a WebAssembly component.
    """
    if "/" in skill or skill.endswith(".py"):
        suggestion = skill
        if skill.endswith(".py"):
            suggestion = skill[:-3]
        if "/" in suggestion:
            suggestion = suggestion.replace("/", ".")

        console.print(
            Panel(
                f"Argument must be a fully qualified Python module name, not [cyan]{skill}[/cyan]\n\n"
                f"[yellow]Did you mean?[/yellow] [green]{suggestion}[/green]\n\n"
                f"[italic]Example: Use [green]my_package.my_module[/green] instead of [red]my_package/my_module.py[/red][/italic]",
                title="[bold red]Error[/bold red]",
                border_style="red",
                padding=(1, 1),
            )
        )
        raise typer.Exit(code=1)

    output_file = f"./{skill.split('.')[-1]}.wasm"
    with Progress(
        SpinnerColumn(),
        TextColumn(
            f"Building WASM component [cyan]{output_file}[/cyan] from module [cyan]{skill}[/cyan]..."
        ),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("", total=None)
        wasm_file = run_componentize_py(skill, output_file, unstable)
        progress.update(task, completed=True)

    if wasm_file and interactive:
        display_publish_suggestion(wasm_file)
        prompt_for_publish(wasm_file)


@app.command()
def publish(
    skill: Annotated[
        str,
        typer.Argument(
            help="A path to a Wasm file containing a Skill.", show_default=False
        ),
    ],
    name: Annotated[
        Optional[str],
        typer.Option(
            help="The name to publish the Skill as. If not provided, it is inferred based on the Wasm filename.",
            show_default="The filename",
        ),
    ] = None,
    tag: Annotated[str, typer.Option(help="An identifier for the Skill.")] = "latest",
) -> None:
    """
    [bold blue]Publish[/bold blue] a skill.

    Publishes a WebAssembly component to the Pharia Skill registry.
    """
    publish_skill(skill, name, tag)


if __name__ == "__main__":
    app()
