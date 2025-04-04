# Quick Start

In this guide, we’ll go through how you can use our Python SDK to build a simple Skill that does a completion request.
The full code can be found [here](https://github.com/Aleph-Alpha/haiku-skill-python/tree/main).

**Prerequisites**

- **Python 3.11** or later ([Download Python](https://www.python.org/downloads/))
- **UV** - Python package installer ([Install UV](https://github.com/astral-sh/uv))

## 1. Installing the SDK

The SDK is published on PyPi.
We recommend using [uv](https://docs.astral.sh/uv/) to manage Python dependencies.
To add the SDK as a dependency to an existing project managed by `uv`, run

We will create an example `haiku` skill, but you can use any name you want for your project.
Create a new project

```sh
uv init haiku && cd haiku
```

and add the SDK as a dependency:

```sh
uv add pharia-skill
```

## 2. Writing a Skill

Now, we are ready to write the skill. Create a file called `haiku.py` and add the following code:

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

We first defined the input and output type as Pydantic models. Then, we create our entrypoint by decorating a function with `@skill`.
This function must stick to the type signature in the example. The [Csi](03-core_concepts.md#csi) which we have defined as the first argument
allows to do all the AI specific interactions with the outside world, in our example a completion request.

## 3. Testing

The `@skill` annotation does not modify the annotated function, which allows the test code to inject different variants of CSI.
The `testing` module provides two implementations of CSI for testing:

- The [DevCsi](https://pharia-skill.readthedocs.io/en/latest/references.html#pharia_skill.testing.DevCsi) can be used for testing Skill code locally against a running Pharia Kernel. See the docstring for how to set it up. It also supports exporting traces to Pharia Studio.
- The [StubCsi](https://pharia-skill.readthedocs.io/en/latest/references.html#pharia_skill.testing.StubCsi) can be used as a base class for mock implementation.

See [core concepts](03-core_concepts.md#testing) for more information on differences between running Skills in the Kernel and locally.
To test against the `DevCsi`, we require two more environment variables:

```sh
# .env
# The address of the PhariaKernel instance you are using, e.g. https://pharia-kernel.{your-pharia-domain}
PHARIA_KERNEL_ADDRESS=https://pharia-kernel.product.pharia.com
# A token to authenticate against PhariaAI, can be retrieved from the PhariaStudio frontend (https://pharia-studio.{your-pharia-domain})
PHARIA_AI_TOKEN=
```

Now, create a `test_haiku.py` file and add the following code:

```python
# test_haiku.py
from haiku import run, Input
from pharia_skill.testing import DevCsi


def test_haiku():
   csi = DevCsi()
   result = run(csi, Input(topic="Oat milk"))
   assert "creamy" in result.haiku or "white" in result.haiku
```

Install pytest:

```sh
uv add pytest --dev
```

And run the test:

```sh
uv run pytest test_haiku.py
```

## 4. Building

You now build your skill, which will produce a `haiku.wasm` file:

```sh
uv run pharia-skill build haiku
```

## 5. Publishing

We are ready to publish the Skill to a registry.
Make sure you understand which namespaces are configured in the Kernel instance you have access to and which registries they are linked with.
For the `p-prod` instance, we have setup a [playground](https://gitlab.aleph-alpha.de/engineering/pharia-kernel-playground) to deploy to.
Make sure to set the required environment variables:

```sh
# .env

# The Kernel supports registries to deploy skills to. See https://pharia-skill.readthedocs.io/en/stable/03-core_concepts.html#namespaces for more details.
# If you are unsure what value to set here, check with the operator of your PhariaAI instance what registries your Kernel is configured with.
SKILL_REGISTRY=registry.gitlab.aleph-alpha.de
SKILL_REPOSITORY=engineering/pharia-kernel-playground/skills

# The `pharia-skill` cli tool uses basic auth to authenticate against the skill registry.
# In case you are using a token as a password, the value of `SKILL_REGISTRY_USER` can be anything.
SKILL_REGISTRY_USER=something
# Skill registry token needs to have read and write access to the registry.
SKILL_REGISTRY_TOKEN=
```

To publish your skill, run

```sh
uv run pharia-skill publish haiku.wasm --name custom_name
```

## 6. Deploying

To know which Skills to serve, the Kernel watches a list of configured namespaces. These can be `toml` files hosted on a server.
If deploying to the [playground](https://gitlab.aleph-alpha.de/engineering/pharia-kernel-playground) , simply update the `namespace.toml` file
in the GitLab UI and add your skill:

```toml
# namespace.toml
skills = [
    { name = "greet" },
    { name = "haiku", tag = "latest" }
]
```

## 7. Invoking via API

Once your skill is deployed, you can test it by making an API call to the Pharia Kernel. You can reference the OpenAPI documentation at `https://pharia-kernel.yourpharia.domain/api-docs` to construct your request.
Here's an example using curl:

```sh
curl 'https://pharia-kernel.yourpharia.domain/v1/skills/{namespace}/{name}/run' \
  --request POST \
  --header 'Content-Type: application/json' \
  --header "Authorization: Bearer $PHARIA_AI_TOKEN" \
  --data '{"topic": "Some text to be a haiku"}'
```
