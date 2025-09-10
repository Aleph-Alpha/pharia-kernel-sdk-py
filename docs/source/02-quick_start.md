# Quick Start

In this guide, we’ll go through how you can use our Python SDK to build a simple Skill that does a chat request.
The full code can be found [here](https://github.com/Aleph-Alpha/haiku-skill-python/tree/main).

**Prerequisites**

- **Python 3.11** or later ([Download Python](https://www.python.org/downloads/))
- **UV** - Python package installer ([Install UV](https://github.com/astral-sh/uv))

## 1. Installing the SDK

The SDK is published on PyPi.
We recommend using [uv](https://docs.astral.sh/uv/) to manage Python dependencies.

We will create an example `haiku` Skill, but you can use any name you want for your project.
Create a new project

```sh
uv init haiku && cd haiku
```

and add the SDK as a dependency:

```sh
uv add pharia-skill
```

## 2. Writing a Skill

Now, we are ready to write the Skill. Create a file called `haiku.py` and add the following code:

```python
# haiku.py
from pharia_skill import Csi, Message, skill
from pydantic import BaseModel


class Input(BaseModel):
   topic: str


class Output(BaseModel):
   haiku: str


@skill
def generate_haiku(csi: Csi, input: Input) -> Output:
   system = Message.system("You are a poet who strictly speaks in haikus.")
   user = Message.user(input.topic)
   response = csi.chat("llama-3.1-8b-instruct", [system, user])
   return Output(haiku=response.message.content.strip())
```

We first define the input and output type as Pydantic models.
Then, we create our entrypoint by decorating a function with `@skill`.
This function must stick to the type signature in the example.
The first argument [Csi](03-core_concepts.md#csi) provides the interface for interacting with the outside world, such as the chat request shown in our example.

## 3. Testing

The `@skill` annotation does not modify the annotated function, which allows the test code to inject different variants of CSI.
The `testing` module provides two implementations of CSI for testing:

- The [DevCsi](https://pharia-skill.readthedocs.io/en/latest/references.html#pharia_skill.testing.DevCsi) can be used for testing Skill code locally against a running PhariaKernel. See the docstring for how to set it up. It also supports exporting traces to PhariaStudio.
- The [StubCsi](https://pharia-skill.readthedocs.io/en/latest/references.html#pharia_skill.testing.StubCsi) can be used as a base class for mock implementation.

See [core concepts](03-core_concepts.md#testing) for more information on differences between running Skills in the Kernel and locally.
To test against the `DevCsi`, we require two more environment variables (optionally one more for tracing):

```sh
# .env

# The address of the PhariaKernel instance you are using, e.g. https://pharia-kernel.your-pharia.domain (replace the `your-pharia.domain` part in all examples)
PHARIA_KERNEL_ADDRESS=

# A token to authenticate against PhariaAI, can be retrieved from the PhariaStudio frontend (https://pharia-studio.your-pharia.domain)
PHARIA_AI_TOKEN=

# The address of the PhariaStudio instance you are using, e.g. https://pharia-studio.your-pharia.domain (replace the `your-pharia.domain` part in all examples)
PHARIA_STUDIO_ADDRESS=
```

Now, create a `test_haiku.py` file and add the following code:

```python
# test_haiku.py
from haiku import generate_haiku, Input
from pharia_skill.testing import DevCsi


def test_haiku():
   csi = DevCsi()
   # optionally with trace export to Studio (creates the project if it does not exist)
   # csi = DevCsi.with_studio("my-project")
   result = generate_haiku(csi, Input(topic="Oat milk"))
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

You now build your Skill, which produces a `haiku.wasm` file:

```sh
uv run pharia-skill build haiku --no-interactive
```

Note that without the `--no-interactive` flag, you will get prompted to optionally publish the Skill.

## 5. Publishing

We are ready to publish the Skill to a registry.
Make sure you understand which namespaces are configured in the PhariaKernel instance you have access to and which registries they are linked with.
For the `p-prod` instance, we have setup a [playground](https://gitlab.aleph-alpha.de/engineering/pharia-kernel-playground) to deploy to.
Make sure to set the required environment variables:

```sh
# .env

# The PhariaKernel supports arbiratry OCI registries to deploy Skills to. See https://pharia-skill.readthedocs.io/en/stable/03-core_concepts.html#namespaces for more details.
# If you are unsure what value to set here, check with the operator of your PhariaAI instance what registries your PhariaKernel is configured with.
# e.g. registry.gitlab.{your-domain} for a gitlab registry, but could also be a GitHub or any other registry that is configured for your PhariaKernel.
SKILL_REGISTRY=

# The repository you want to deploy your Skill to.
# e.g. engineering/your-team/skills
SKILL_REPOSITORY=

# The `pharia-skill` CLI tool uses basic auth to authenticate against the Skill registry.
# In case you are using a token as a password, the value of `SKILL_REGISTRY_USER` can be anything, e.g. `dummy`.
SKILL_REGISTRY_USER=
# A token that has read and write access to the registry you want to publish your Skill to.
SKILL_REGISTRY_TOKEN=
```

To publish your Skill, run:

```sh
uv run pharia-skill publish haiku.wasm --name custom_name
```

## 6. Deploying

To know which Skills to serve, the PhariaKernel watches a list of configured namespaces. These can be `toml` files hosted on a server.
Check with your operator where this configuration file for the namespace that you deployed to in the previous step is hosted.
Then, update the configuration file and add your Skill:

```toml
# namespace.toml
skills = [
    { name = "greet" },
    { name = "haiku", tag = "latest" }
]
```

## 7. Invoking via API

Once your Skill is deployed, you can test it by making an API call to the PhariaKernel. You can reference the OpenAPI documentation at `https://pharia-kernel.yourpharia.domain/api-docs` to construct your request. You need to provide the name of the `namespace` that you have previously deployed your Skill to. If unsure, check with your operator. Here's an example using curl:

```sh
curl 'https://pharia-kernel.yourpharia.domain/v1/skills/{namespace}/{name}/run' \
  --request POST \
  --header 'Content-Type: application/json' \
  --header "Authorization: Bearer $PHARIA_AI_TOKEN" \
  --data '{"topic": "Some text to be a haiku"}'
```
