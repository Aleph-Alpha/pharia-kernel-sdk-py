# Pharia Kernel Python SDK

You build your skill in Python, which is then compiled into a Wasm module.
Then, the skill is deployed to an [instance of Pharia Kernel](https://pharia-kernel.product.pharia.com),
where it can be invoked on demand.
To this end, this SDK provides some tooling and APIs for skill development.

You can access the [Documentation](https://aleph-alpha-pharia-kernel-sdk-py.readthedocs-hosted.com/en/latest/index.html)
with your GitHub account.

## Installing SDK

The SDK is distributed via the Aleph Alpha Artifactory PyPI. You may need to request a JFrog account, or extend the permission of your JFrog account via the [Product Service Desk](https://aleph-alpha.atlassian.net/servicedesk/customer/portals).

```shell
python -m venv .venv
source .venv/bin/activate
pip install --extra-index-url https://alephalpha.jfrog.io/artifactory/api/pypi/python/simple pharia-kernel-sdk-py
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
poetry install
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
