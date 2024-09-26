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

You now create the file `haiku.wasm`, ready to be uploaded.

```shell
pip install componentize-py
componentize-py -w skill componentize haiku -o ./haiku.wasm -p . -p wasi_deps
```

## Deploying Skills

Pharia Skill is provided as a tool for deploying Skills.

```shell
podman login alephalpha.jfrog.io/pharia-kernel-images -u $JFROG_USER -p $JFROG_PASSWORD
podman pull alephalpha.jfrog.io/pharia-kernel-images/pharia-skill:latest
podman tag alephalpha.jfrog.io/pharia-kernel-images/pharia-skill:latest pharia-skill
```

With the tooling available, you can now upload the Skill. e.g. for the `playgound` namespace, a skill registry is provided at <https://gitlab.aleph-alpha.de/engineering/pharia-kernel-playground>.

```shell
podman run -v ./haiku.wasm:/haiku.wasm pharia-skill publish -R registry.gitlab.aleph-alpha.de -r engineering/pharia-kernel-playground/skills -u DUMMY_USER_NAME -p $GITLAB_TOKEN -t latest ./haiku.wasm
```

## Configuring namespace

We have to configure the `namespace.toml` for the deployed skills to be loaded in Pharia Kernel.
We have to extend the existing `skills` entries by providing the `name` and the optional `tag` fields.

```toml
# namespace.toml
skills = [{ name = "haiku", tag = "latest" }]
```
