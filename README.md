# Pharia Kernel Python SDK

You build your skill in Python, which is then compiled into a Wasm module.
Then, the skill is deployed to an [instance of Pharia Kernel](https://pharia-kernel.product.pharia.com),
where it can be invoked on demand.
To this end, this SDK provides some tooling and APIs for skill development.

You can access the [Documentation](https://aleph-alpha-pharia-kernel-sdk-py.readthedocs-hosted.com/en/latest/index.html)
with your GitHub account.

## Installing the SDK

While we are planning to open source the SDK soon, it is currently distributed via the Aleph Alpha Artifactory PyPI.
To install it, you need a JFrog account and need to create an access token in the UI.
We recommend using [uv](https://docs.astral.sh/uv/) to install the SDK.

To add the SDK as a dependency to an existing project managed by `uv`, first create a `.env` file and set the needed environment variables:

```sh
# .env
UV_INDEX_JFROG_USERNAME=your-username
UV_INDEX_JFROG_PASSWORD=$JFROG_TOKEN
```

Then, add the SDK as a dependency:

```sh
set -a && source .env
uv add --index jfrog=https://alephalpha.jfrog.io/artifactory/api/pypi/python/simple pharia-kernel-sdk-py
```

## Developing Skills in Python

The `pharia_skill` package provides a decorator to support skill development.
The decorator inserts the Cognitive System Interface (CSI), which always need to be specified as the first argument.
As an example, we write a new skill in `haiku.py`.

```python
# haiku.py
from pharia_skill import ChatParams, Csi, Message, skill
from pydantic import BaseModel


class Input(BaseModel):
    topic: str


class Output(BaseModel):
    haiku: str


@skill
def run(csi: Csi, input: Input) -> Output:
    system = Message.system("You are a poet who strictly speaks in haikus.")
    user = Message.user(input.topic)
    params = ChatParams(max_tokens=64)
    response = csi.chat("llama-3.1-8b-instruct", [system, user], params)
    return Output(haiku=response.message.content.strip())
```

### Chat Interface & Conversational Search

The [OpenAI Chat API](https://platform.openai.com/docs/api-reference/chat) is emerging as a standard to expose conversational interface of LLMs.
This API is also offered in the `Csi` with the `chat` method. Leveraging this, you can easily expose your own custom flavoured chat API as a Kernel Skill.
Note that you can return expose internal datatypes in the interface of you skill as long as they are wrapped in a `Pydantic` model:

```python
from pharia_skill import Csi, Message, skill

class ChatInterface(BaseModel):
    message: list[Message]

@skill
def run(csi: Csi, input: ChatInterface) -> ChatInterface:
    # Alter the input message in any way to apply your own flavour
    # You could add a search lookup to allow conversational search, or just 
    # prepend a custom system prompt
    input = apply_flavour(input)
    return csi.chat("llama-3.1-8b-instruct", input.messages)
```

Now, you can directly point a compatible UI at your skill endpoint and start chatting.

### Testing

The `@skill` annotation does not modify the annotated function, which allows the test code to inject different variants of CSI.
The `testing` module provides two implementations of CSI for testing:

- The `DevCsi` can be used for testing Skill code locally against a running Pharia Kernel. See the docstring for how to set it up. It also supports exporting traces to Pharia Studio.
- The `StubCsi` can be used as a base class for mock implementation.

### Compiling Skill to Wasm

You now build your skill, which will produce a `haiku.wasm` file:

```shell
pharia-skill build examples.haiku
```

## Deploying Skills

Pharia Skill is provided as a tool for deploying Skills. For deployment, you need to set the `JFROG_USER` and `JFROG_TOKEN` environment variables in your environment. The `JFROG_USER` is your email address. The `JFROG_TOKEN` can be created in the JFrog UI in your personal settings. You also need to set `SKILL_REGISTRY_USER`, `SKILL_REGISTRY_TOKEN`, `SKILL_REGISTRY`, and `SKILL_REPOSITORY`. The token must have access to the registry where the skill is deployed to. We have setup a [playground](https://gitlab.aleph-alpha.de/engineering/pharia-kernel-playground) to deploy to, so you can set the variables to

```shell
SKILL_REGISTRY=registry.gitlab.aleph-alpha.de
SKILL_REPOSITORY=engineering/pharia-kernel-playground/skills
```

To deploy your skill, run

```shell
pharia-skill publish haiku
```

## Configuring namespace

We have to configure the `namespace.toml` for the deployed skills to be loaded in Pharia Kernel.
We have to extend the existing `skills` entries by providing the `name` and the optional `tag` fields.

```toml
# namespace.toml
skills = [
    { name = "greet" },
    { name = "haiku", tag = "latest" }
]
```

## Contributing

Install the dependencies with

```shell
uv sync --dev
```

We use [pre-commit](https://pre-commit.com/) to check that code is formatted, linted and type checked. You can initialize by simply typing

```shell
pre-commit
pre-commit install
```

Verify that it is running with

```shell
pre-commit run --all-files
```
