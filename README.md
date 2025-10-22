# PhariaSkill

PhariaEngine is a serverless AI runtime that hosts AI code as isolated WebAssembly components called "Skills". With this SDK, you write Python functions (using simple decorators), compile them to WebAssembly, and push them to an OCI registry.
The Engine then runs your code serverless-style, providing access to inference and tools hosted by MCP servers.

## Documentation & Resources

- **[Full Documentation](https://pharia-skill.readthedocs.io/en/latest/)** - Complete guides, tutorials, and concepts
- **[API Documentation](https://pharia-kernel.product.pharia.com/api-docs)** - Engine HTTP API reference for invoking Skills
- **[Examples](examples/)** - Sample Skills demonstrating various use cases

## Why WebAssembly?

- **Simpler deployment**: No Dockerfiles, base images, or web servers
- **Faster cold starts**: WebAssembly boots in milliseconds, not seconds
- **Reduced complexity**: The runtime manages authentication, scaling, connection to MCP servers, etc.
- **Isolation of concerns**: Skill code is focused on pure methodology
- **Observability**: Because all interactions are mediated by the Engine, it can provide tracing and metrics.

The tradeoff is constraints - you can't install arbitrary (native) dependencies or make network calls directly.
Everything goes through the interface offered by the Engine - the Cognitive System Interface (CSI).

## Installation

```sh
uv add pharia-skill
```

In case you want to use changes in the SDK that have not been released yet, you can add the SDK as a git dependency:

```sh
uv add git+https://github.com/aleph-alpha/pharia-skill.git
```

## Basic Example

```python
from pydantic import BaseModel
from pharia_skill import skill, Csi, Message, ChatParams

class Input(BaseModel):
    topic: str

class Output(BaseModel):
    response: str

@skill
def generate_summary(csi: Csi, input: Input) -> Output:
    messages = [Message.user(f"Summarize this topic in 2 sentences: {input.topic}")]
    response = csi.chat("llama-3.1-8b-instruct", messages, ChatParams(max_tokens=100))
    return Output(response=response.message.content)
```

That's it. The Engine will inject the `Csi` interface and will deserialize the input from the HTTP request.

## Streaming Agent

This example assumes that the Engine is configured with MCP servers that provide the `search` and `fetch` tools.

```python
from pydantic import BaseModel
from pharia_skill import Csi, Message, MessageWriter, message_stream

class Input(BaseModel):
    messages: list[Message]

@message_stream
def web_search(csi: Csi, writer: MessageWriter[None], input: Input) -> None:
    model = "llama-3.3-70b-instruct"
    with csi.chat_stream(model, input.messages, tools=["search", "fetch"]) as response:
        writer.forward_response(response)
```

## Development Workflow

### Testing

If you have access to a PhariaEngine instance, you can test your Skill locally, as the CSI is also offered via HTTP via the `DevCsi`:

```python
from pharia_skill import DevCsi
# Assuming you have a Skill called `my_skill` that takes an `Input` model
from my_skill import my_skill, Input

def test_my_skill():
    csi = DevCsi()
    test_input = Input(question="What is the capital of France?")
    result = my_skill(csi, test_input)
    assert result.answer == "Paris"
```

### Building and Publishing

Once you are happy with your Skill, you can build it and publish it to an OCI registry.

```sh
# Build WebAssembly component
pharia-skill build my_skill.py

# Publish to an OCI registry
pharia-skill publish my-skill.wasm
```

### Running

This SDK builds a WebAssembly component targeting the `pharia:skill` [WIT](https://component-model.bytecodealliance.org/design/wit.html) world.
That means a WebAssembly runtime offering this interface is required to run your Skill. The Engine is such a runtime.
To deploy your Skill, add your Skill to the configuration file of your namespace.
Then, you can invoke it via the HTTP API of the Engine. For example:

```sh
curl -X POST http://pharia-kernel.my-pharia-ai-cluster.com/v1/skills/{namespace}/my-skill/run \
     -H "Content-Type: application/json" \
     -d '{"question": "What is the capital of France?"}'
```
