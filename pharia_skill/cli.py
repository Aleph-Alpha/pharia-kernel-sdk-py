import logging
import os
import subprocess
import time
from enum import Enum
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
    PYDANTIC_CORE_VERSION = "2.33.2"
    WASI_DEPS_PATH = "wasi_deps"
    if os.path.exists(WASI_DEPS_PATH):
        if not os.path.exists(
            f"{WASI_DEPS_PATH}/pydantic_core-{PYDANTIC_CORE_VERSION}.dist-info"
        ):
            logger.info("Deleting outdated Pydantic WASI wheels...")
            subprocess.run(["rm", "-rf", WASI_DEPS_PATH])

    if not os.path.exists(WASI_DEPS_PATH):
        logger.info("Downloading Pydantic WASI wheels...")
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
    """Any error encountered trying to build the Skill as a Wasm component."""

    def __init__(self, message: str):
        self.message = message


class IsMessageStream(BuildError):
    """Skill needs to be built against the `message-stream-skill` world."""

    def __init__(self, message: str):
        self.message = message


class IsSkill(BuildError):
    """Skill is not build against the `skill` world."""

    def __init__(self, message: str):
        self.message = message


class NoHttpError(BuildError):
    """Skill imports requests, which is currently not supported."""

    def __init__(self, message: str):
        self.message = message


class SkillType(str, Enum):
    SKILL = "skill"
    MESSAGE_STREAM_SKILL = "message-stream-skill"


def run_componentize_py(
    skill_module: str, output_file: str, unstable: bool, skill_type: SkillType
) -> str:
    """Build the skill to a Wasm component using componentize-py.

    The call to componentize-py targets the `skill` wit world and adds the downloaded
    Pydantic WASI wheels to the Python path.

    Returns:
        str: The path to the generated Wasm file.
    """
    setup_wasi_deps()
    args = ["--all-features"] if unstable else []
    command = [
        "componentize-py",
        *args,
        "-w",
        skill_type.value,
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
        if (
            "ModuleNotFoundError: No module named 'pharia_skill.bindings.exports.message_stream'"
            in e.stderr
        ):
            raise IsMessageStream(e.stderr)
        if (
            "ModuleNotFoundError: No module named 'pharia_skill.bindings.exports.skill_handler'"
            in e.stderr
        ):
            raise IsSkill(e.stderr)

        if "ModuleNotFoundError: No module named 'zlib'" in e.stderr:
            raise NoHttpError(e.stderr)

        raise BuildError(e.stderr)
    return output_file


def display_publish_suggestion(wasm_file: str) -> None:
    """Display a colorful suggestion to publish the skill.

    Args:
        wasm_file: Path to the generated Wasm file.
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
        skill_path: Path to the Wasm file to publish.
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
        wasm_file: Path to the generated Wasm file.
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
    skill_type: Annotated[
        SkillType,
        typer.Option(
            help="The type of skill to build.",
            show_default=True,
        ),
    ] = SkillType.SKILL,
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
            f"Building Wasm component [cyan]{output_file}[/cyan] from module [cyan]{skill}[/cyan]..."
        ),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("", total=None)
        try:
            wasm_file = run_componentize_py(skill, output_file, unstable, skill_type)
            progress.update(task, completed=True)
        except IsMessageStream:
            console.print(
                Panel(
                    "It seems you are trying to build a Skill with the @message_stream decorator.\nPlease ensure to set the --skill-type flag to [green]message-stream-skill[/green].",
                    title="[bold red]Error[/bold red]",
                )
            )
            raise typer.Exit(code=1)
        except IsSkill:
            console.print(
                Panel(
                    "It seems you are trying to build a Skill decorated with the @skill decorator.\nPlease ensure to set the --skill-type flag to [green]skill[/green].",
                    title="[bold red]Error[/bold red]",
                )
            )
            raise typer.Exit(code=1)
        except NoHttpError:
            console.print(
                Panel(
                    "It seems you are trying to build a Skill that imports a library that does [red]outbound http[/red] requests.\nThis is currently not supported.\nPlease remove the corresponding import for the build to succeed.",
                    title="[bold red]Error[/bold red]",
                )
            )
            raise typer.Exit(code=1)
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
