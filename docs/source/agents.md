# Agents

```{image} ../../_static/agent.png
:alt: Sloth Agent
:width: 200px
```

The Kernel is developed with an agent focus in mind. There are many challenges with running agents in production settings. A given function could consume all of the resources of the system, be caught in an infinite loop, or attempt to access resources that it should not.

A common way to mitigate these risks it to run the code in a sandboxed environment. It places constraints on the code that is run, but it provides the benefit of having a system that can be trusted to automate more and more business processes.

WASM, along with its WASI (WebAssembly System Interface) specification provides a compelling security approach to handling these risks. Each executable can only access what is has been granted access to. Whether compute resources, execution time, files, network access, or other resources, the WASI interface provides a way to control what the code can do, and it is also clear what permissions have been granted.

## Function Calling

The first step to support agent-like workflows in the Kernel is to provide models the ability to call functions. This involves usually three steps:

1. Users can defined so called tools which are passed to the model.
2. The model may or may not decide to respond with a tool call.
3. If the model requests a tool call, the user can execute the tool and pass the result back to the model.

## Code Execution

The Kernel already offers a `CodeInterpreter`, so the ability to run code that the LLM has produced.
Because the Python Interpreter that execute this code runs in WASM, there are tight controls to what the code can do.