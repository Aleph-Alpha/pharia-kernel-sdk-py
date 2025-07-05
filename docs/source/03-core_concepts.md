# Core Concepts

There is a few concepts which arise when talking about the Kernel

## Skill

A Skill is the fundamental building block within the Kernel, encapsulating a discrete unit of business or AI logic. It is a is a user-defined stateless function that adheres to strict input/output schemas defined using Pydantic models. This ensures type safety, validation, and clear documentation of the Skill’s contract.

Unlike traditional serverless or FaaS (Function as a Service) functions, Skills are designed to operate within the Kernel’s orchestration layer. They interact with the broader system through the Cognitive System Interface (CSI) defined below, which exposes AI-native capabilities like LLM inference, vector search, and authenticated data access. This abstraction allows Skills to focus purely on business logic while delegating infrastructure concerns to the Kernel.

When this Skill will get executed, and how, is up to the Kernel, which allows the engineer to focus on the business and AI logic of the Skill at hand.

## Wasm Component

On a more technical level, when you build your Skill, it is compiled to a [Wasm Component](https://component-model.bytecodealliance.org/).
Under the hood, we use [componentize-py](https://github.com/bytecodealliance/componentize-py?tab=readme-ov-file#known-limitations) to do that.
`componentize-py` resolves the imports of a Skill module, so any package you import in you Skill will also be included in the Component.
However, non-native dependencies (e.g. `NumPy` which is written in `C`) only work if the wheels for [WASI targets](https://github.com/benbrandt/wasi-wheels) are available at build-time. For `Pydantic`, our SDK resolves this under the hood for you.

## CSI

Similar to how an operating system provides functionality to applications, the Cognitive System Interface (CSI) is the set of functions provided to the user code when it is run within the Kernel environment.
The functionality of the CSI is focussed around the needs of AI methodology, such as LLM inference, vector search, and data access.

By providing a common interface to these tools, it provides the opportunity for the user code to describe the intended interaction and outcome in their code, and the Kernel is able to take care of the complexity of providing it.
For example, authentication is not part of the [CSI](https://pharia-skill.readthedocs.io/en/latest/references.html#pharia_skill.Csi) interface, but is handled by the Kernel, which will authenticate all CSI calls with the token provided in the request.
To make this interface available at development time, the SDK provides a [DevCSI](https://pharia-skill.readthedocs.io/en/latest/references.html#pharia_skill.testing.DevCsi).

### Testing

When Skills are run in the Kernel, the CSI is provided via an Application Binary Interface. This interface is defined via the [Wasm Interface Type](https://component-model.bytecodealliance.org/design/wit.html) (WIT) language.
For development and debugging, Skills can also run in a local Python environment. The CSI which is available to the Skill at runtime can be substituted with a [DevCSI](https://pharia-skill.readthedocs.io/en/latest/references.html#pharia_skill.testing.DevCsi) which is backed by HTTP requests against a running instance of the Kernel.
Developers can write tests, step through their Python code and inspect the state of variables.

### Tracing

The Kernel automatically traces Skills and all interactions with the CSI (logs are currently not available). When developing Skills, the developer does not need to worry about setting up tracing.
The Kernel can be configured to export traces to an OpenTelemetry compatible backend. At development time, the [DevCSI](https://pharia-skill.readthedocs.io/en/latest/references.html#pharia_skill.testing.DevCsi) can be configured to export traces to Pharia Studio, where they can be visualized.

## Namespaces

The Kernel has the concept of namespaces, which are used to group Skills. Namespaces are configured by the operator of the Kernel.
For each namespace, the operator specifies two things:

1. An OCI registry to load Skills from (Skills are not containers. Yet, we still publish them as OCI images to registries)
2. A namespace configuration (a toml file, typically checked into a Git repository)

This allows teams to deploy their Skills in self-service, after a namespace has been configured by the operator.
Permissions for the registry and the namespace configuration could be configured in such a way that only team members can deploy Skills to the namespace.
In order to make a Skill available in the Kernel two criteria need to be met, the Skill must be deployed as a component to an OCI registry and the Skill must be configured in the namespace configuration.

You can check out `pharia-kernel.namespaces` in the `values.yaml` of the respective deployment. For deployment, configure the `pharia-skill` CLI tool with environment variables to point to the correct registry for the namespace you want to deploy to.

## Tool Calling

PhariaKernel allows Skill to invoke tools via the [invoke_tool](https://pharia-skill.readthedocs.io/en/latest/_modules/pharia_skill/csi/csi.html#Csi.invoke_tool) method of the `Csi`.
The list of available tools for a particular namespace can be queried via a GET request to the `v1/tools/{namespace}` route of PhariaKernel.

### Native tools

PhariaKernel offers native tools that are built-in and optionally configurable for each namespace.

Currently, the available tools are `add`, `subtract`, and `saboteur`, which are intended for testing during skill development:

```json
native-tools = [ "add", "subtract", "saboteur" ]
```

### MCP servers

PhariaKernel allows additional tools to be provided via the Model Context Protocol (MCP).

All MCP servers that use Streamable HTTP transport and do not require authentication can be configured for each namespace:

```json
mcp-servers = [
    "https://gitmcp.io/Aleph-Alpha/pharia-kernel-sdk-py",
    "http://mcp-fetch.pharia-ai.svc.cluster.local:8000/mcp"
]
```