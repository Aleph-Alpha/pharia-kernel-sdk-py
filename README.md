# Pharia Kernel Python SDK

You build your skill in Python, which is then compiled into a Wasm module. Then, the skill is deployed to Pharia Kernel, where it can be invoked on demand. To this end, this SDK provides some tooling and APIs for skill development.

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
from pharia_skill import CompletionParams, Csi, skill
from pydantic import BaseModel


class Input(BaseModel):
    topic: str


@skill
def haiku(csi: Csi, input: Input) -> str:
    prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

    You are a poet who strictly speaks in haikus.<|eot_id|><|start_header_id|>user<|end_header_id|>

    {input.topic}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""
    params = CompletionParams(max_tokens=64)
    completion = csi.complete("llama-3.1-8b-instruct", prompt, params)
    return completion.text.strip()
```

### Testing

The `@skill` annotation does not modify the annotated function, which allows the test code to inject different variants of CSI.
The `testing` module provides two implementations of CSI for testing:

- The `DevCsi` can be used for testing Skill code locally against a running Pharia Kernel. See the docstring for how to set it up.
- The `StubCsi` can be used as a base class for mock implementation.

### Running via HTTP

If you want to expose your skill via HTTP locally, you can run

```shell
pharia-skill up examples.haiku
```

This will expose your skill under the `execute_skill` path, similar to how it is exposed by the Kernel.
You must provide the name of the skill function as skill name on invocation. Provided namespaces are ignored on invocation.

## Building Skills

When building the skills, the wheels that include native dependencies need to be provided additionally for Wasm. For example, the skill SDK has a dependency on `pydantic` v2.5.2.

### Download Pydantic WASI wheels

Supported Pydantic versions:

```toml
pydantic-core = "2.14.5"
pydantic = "2.5.2"
```

Download and unpack WASI wheels (without installation):

```shell
mkdir wasi_deps
cd wasi_deps
curl -OL https://github.com/dicej/wasi-wheels/releases/download/latest/pydantic_core-wasi.tar.gz
tar xf pydantic_core-wasi.tar.gz
cd ..
```

### Compiling Skill to Wasm

You now build your skill, which will produce a `haiku.wasm` file:

```shell
pharia-skill build examples.haiku
```

## Deploying Skills

Pharia Skill is provided as a tool for deploying Skills. For deployment, you need to set the `JFROG_USER` and `JFROG_PASSWORD` environment variables in your environment. You also need to set `GITLAB_TOKEN` and `SKILL_REGISTRY` and `SKILL_REPOSITORY`. The gitlab token must have access to the registry where the skill is deployed to. We have setup a [playground](https://gitlab.aleph-alpha.de/engineering/pharia-kernel-playground) to deploy to, so you can set the variables to

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
skills = [{ name = "haiku", tag = "latest" }]
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