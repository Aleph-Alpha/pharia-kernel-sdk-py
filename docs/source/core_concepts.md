# Core Concepts

There is a few concepts which arise when talking about the Kernel

## Skill

The first of these primitives is a Skill. A Skill is a user-defined function that follows the request/response pattern: It takes some input, and returns some output.

A Skill has a well-defined schema for input and output. What makes it different from a normal Serverless or FaaS (Function as a Service) function is that because it is being run in the context of the Kernel, it will have access to the Cognitive System Interface (CSI), to be defined below.

When this Skill will get executed, and how, is up to the Kernel, which allows the engineer to focus on the business and AI logic of the Skill at hand.

## WASM Component

On a more technical level, when you build your Skill, it is compiled to a [WASM Component](https://component-model.bytecodealliance.org/).
Under the hood, we use [componentize-py](https://github.com/bytecodealliance/componentize-py?tab=readme-ov-file#known-limitations) to do that.
`componentize-py` resolves the imports of a Skill module, so any package you import in you Skill will also be included in the Component.
However, non-native dependencies (e.g. `NumPy` which is written in `C`) only work if the wheels for [WASI targets](https://github.com/benbrandt/wasi-wheels) are available at build-time. For `Pydantic`, our SDK resolves this under the hood for you.

## CSI

The Cognitive System Interface, or CSI, is the set of functionality that is provided to the user code when it is run within the Kernel environment.
So the engineer is able to import and call functions that are provided by the Kernel; functionality related to AI, data, and other services.

By providing a common interface to these tools, it provides the opportunity for the user code to describe the intended interaction and outcome in their code, and the Kernel is able to take care of the complexity of providing it.

## Namespaces

The Kernel has the concept of namespaces, which are used to group Skills. Namespaces are configured by the operator of the Kernel.
For each namespace, the operator specifies two things:

1. An OCI registry to load Skills from (Skills are not containers. Yet, we still publish them as OCI images to registries)
2. A namespace configuration (a toml file, typically checked into a Git repository)

This allows teams to deploy their Skills in self-service, after a namespace has been configured by the operator.
Permissions for the registry and the namespace configuration could be configured in such a way that only team members can deploy Skills to the namespace.
In order to make a Skill available in the Kernel two criteria need to be met, the Skill must be deployed as a component to an OCI registry and the Skill must be configured in the namespace configuration.

At Aleph Alpha, you can check out the configured namespaces in the [values.yaml](https://gitlab.aleph-alpha.de/product/p-prod-deployment/-/blob/main/applications/pharia-ai/values.yaml?ref_type=heads#L813) of the deployment. You configure the `pharia-skill` CLI tool with environment variables to point to the correct registry for the namespace you want to deploy to.
