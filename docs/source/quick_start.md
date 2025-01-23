# Quick Start

In this guide, we’ll go through how you can use our Python SDK to build a simple Skill that does a completion request.
The full code can be found [here](https://github.com/Aleph-Alpha/haiku-skill-python/tree/main).

## 1. Installing the SDK

While we are planning to open source the SDK soon, it is currently distributed via the Aleph Alpha Artifactory PyPI.
To install it, you need a JFrog account and need to create an access token in the UI.
We recommend using [uv](https://docs.astral.sh/uv/) to install the SDK. Set these two environment variables:

```sh
export UV_INDEX_JFROG_USERNAME=your-username
export UV_INDEX_JFROG_PASSWORD=your-password
```

Then, run the following command to add the SDK as a dependency to your project:

```sh
uv add --index-url https://alephalpha.jfrog.io/artifactory/api/pypi/python/simple pharia-kernel-sdk-py
```

## 2. Writing a Skill

Now, we are ready to write the skill. Create a file called `haiku.py` and add the following code:

```python
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
This function must stick to the type signature in the example. The [Csi](references.rst#pharia_skill.Csi) which we have defined as the first argument
allows to do all the AI specific interactions with the outside world, in our example a completion request.

## 3. Testing

The `@skill` annotation does not modify the annotated function, which allows the test code to inject different variants of CSI.
The `testing` module provides two implementations of CSI for testing:

- The [DevCsi](references.rst#pharia_skill.testing.DevCsi) can be used for testing Skill code locally against a running Pharia Kernel. See the docstring for how to set it up. It also supports exporting traces to Pharia Studio.
- The [StubCsi](references.rst#pharia_skill.testing.DevCsi) can be used as a base class for mock implementation.

## 4. Building

You now build your skill, which will produce a `haiku.wasm` file:

```sh
pharia-skill build haiku
```

## 5. Publishing

We are ready to publish the Skill to a registry.
Make sure you understand which namespaces are configured in the Kernel instance you have access to and which registries they are linked with.
For the `p-prod` instance, we have setup a [playground](https://gitlab.aleph-alpha.de/engineering/pharia-kernel-playground) to deploy to.
Make sure to set the required environment variables:

```sh
SKILL_REGISTRY_USER=
SKILL_REGISTRY_TOKEN=
SKILL_REGISTRY=registry.gitlab.aleph-alpha.de
SKILL_REPOSITORY=engineering/pharia-kernel-playground/skills
```

To publish your skill, run

```sh
pharia-skill publish haiku
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