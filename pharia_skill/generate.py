import json
import os
from pathlib import Path

import inflection
import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from typing_extensions import Annotated

app = typer.Typer(rich_markup_mode="rich")

console = Console()


@app.callback()
def callback() -> None:
    """
    [bold blue]Generate[/bold blue] a skill.

    Generate skill code from a template.
    """


@app.command()
def list() -> None:
    """
    [bold blue]List[/bold blue] all available skill templates.
    """

    console.print(
        Panel.fit(
            "[bold]Chat:[/bold] [cyan]A streaming skill with a chat interface.[/cyan]\n",
            title="[bold green]Available Templates[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
    )


@app.command()
def reload(
    config: Annotated[
        Path,
        typer.Option(
            help="The template configuration file to generate the skill with.",
        ),
    ] = Path("template_config.json"),
    interactive: Annotated[
        bool,
        typer.Option(
            help="Confirm for overwriting file.",
            show_default=True,
        ),
    ] = True,
) -> None:
    """
    [bold blue]Generate[/bold blue] a skill based on an existing template configuration file.
    """

    if not os.path.exists(config):
        print(
            f"{config} not found. Run `pharia-skill generate list` to see available templates."
        )
        raise typer.Exit(code=1)

    with open(config, "r") as f:
        template_config = json.load(f)
        output = template_config["output"]
        if interactive and os.path.exists(output):
            typer.confirm(f"{output} already exists. Overwrite?", abort=True)
        template = template_config["template"]
        match template:
            case "chat":
                generate_chat_skill(**template_config)
            case _:
                raise typer.Exit(code=1)


@app.command()
def chat(
    name: Annotated[
        str | None,
        typer.Option(
            help="The name of the skill.",
        ),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option(
            help="The output file of the skill.",
        ),
    ] = None,
    config: Annotated[
        Path | None,
        typer.Option(
            help="The template configuration file that contains the values for the generated skill.",
        ),
    ] = None,
    model: Annotated[
        str | None,
        typer.Option(
            help="The model to use for the skill.",
        ),
    ] = None,
    system_prompt: Annotated[
        str | None,
        typer.Option(
            help="The system prompt to use for the skill.",
        ),
    ] = None,
    interactive: Annotated[
        bool,
        typer.Option(
            help="Prompt for template values.",
            show_default=True,
        ),
    ] = True,
) -> None:
    """
    [bold blue]Generate[/bold blue] a chat skill from a template.
    """

    if not name:
        default_name = "skill"
        name = (
            Prompt.ask(
                "[bold cyan]Skill name[/bold cyan]",
                default=default_name,
                show_default=True,
            )
            if interactive
            else default_name
        )

    if not output:
        default_output = f"{inflection.underscore(name)}.py"
        output = Path(
            Prompt.ask(
                "[bold cyan]Output file[/bold cyan]",
                default=default_output,
                show_default=True,
            )
            if interactive
            else default_output
        )

    if not config:
        default_config = "template_config.json"
        config = Path(
            Prompt.ask(
                "[bold cyan]Template config[/bold cyan]",
                default=default_config,
                show_default=True,
            )
            if interactive
            else default_config
        )

    if not model:
        default_model = "llama-3.1-8b-instruct"
        model = (
            Prompt.ask(
                "[bold cyan]Model[/bold cyan]",
                default=default_model,
                show_default=True,
            )
            if interactive
            else default_model
        )

    if not system_prompt:
        default_system_prompt = "You are a helpful assistant."
        system_prompt = (
            Prompt.ask(
                "[bold cyan]System prompt[/bold cyan]",
                default=default_system_prompt,
                show_default=True,
            )
            if interactive
            else default_system_prompt
        )

    if interactive:
        output_exists = os.path.exists(output)
        config_exists = os.path.exists(config)
        if output_exists and config_exists:
            typer.confirm(
                f"{output} and {config} already exist. Overwrite?", abort=True
            )
        elif output_exists:
            typer.confirm(f"{output} already exists. Overwrite?", abort=True)
        elif config_exists:
            typer.confirm(f"{config} already exists. Overwrite?", abort=True)

    generate_chat_skill(output, model, system_prompt)

    with open(config, "w") as f:
        json.dump(
            {
                "template": "chat",
                "template_version": "0.1.0",
                "version": "0.1.0",
                "name": name,
                "output": str(output),
                "model": model,
                "system_prompt": system_prompt,
            },
            f,
            indent=2,
        )


def generate_chat_skill(output: Path, model: str, system_prompt: str) -> None:
    with open(output, "w") as f:
        f.write(f'''# generated by pharia-skill
from pydantic import BaseModel, Field, field_validator

from pharia_skill import (
    ChatParams,
    Csi,
    Message,
    MessageWriter,
    Role,
    message_stream,
)

MODEL = "{model}"
SYSTEM_PROMPT = "{system_prompt}"


class SkillInput(BaseModel):
    """The conversation history between the user and the assistant."""

    messages: list[Message] = Field(..., min_length=1)

    @field_validator("messages")
    @classmethod
    def validate_no_system_messages(cls, messages: list[Message]) -> list[Message]:
        """Validate that no system messages are present in the message list."""

        if any(message.role == Role.System for message in messages):
            raise ValueError(
                "System messages are not allowed in the conversation history."
            )
        return messages


@message_stream
def chat_skill(csi: Csi, writer: MessageWriter[None], input: SkillInput) -> None:
    """A skill that streams a response."""

    messages = [
        Message.system(SYSTEM_PROMPT),
        *input.messages,
    ]
    # TODO: summarize messages if above context threshold
    params = ChatParams()
    with csi.chat_stream(MODEL, messages, params) as response:
        writer.forward_response(response)

''')
