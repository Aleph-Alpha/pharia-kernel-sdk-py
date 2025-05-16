# LLM Code Execution

The Kernel offers a [CodeInterpreter](https://pharia-skill.readthedocs.io/en/latest/references.html#pharia_skill.llama3.CodeInterpreter), so the ability to run code that the LLM has produced.
Because the Python Interpreter that executes this code runs in Wasm, there are tight controls to what the code can do. It provides a secure, sandboxed environment for executing code, ensuring that it does not have access to sensitive data or perform unauthorized actions.

## Limitations

Outbound HTTP requests are currently not supported in the Kernel. This means tools that need to make HTTP requests can only be executed in a local environment with the [DevCsi](https://pharia-skill.readthedocs.io/en/latest/references.html#pharia_skill.testing.DevCsi) class and not be deployed to the Kernel.
