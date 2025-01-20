# Core Concepts

There is a few concepts which arise when talking about the Kernel

## Skill

The first of these primitives is a Skill. A Skill is a user-defined function that follows the request/response pattern: It takes some input, and returns some output.

A Skill has a well-defined schema for input and output. What makes it different from a normal Serverless or FaaS (Function as a Service) function is that because it is being run in the context of the Kernel, it will have access to the Cognitive System Interface (CSI), to be defined below.

When this Skill will get executed, and how, is up to the Kernel, which allows the engineer to focus on the business and AI logic of the Skill at hand.

## CSI

The Cognitive System Interface, or CSI, is the set of functionality that is provided to the user code when it is run within the Kernel environment.
So the engineer is able to import and call functions that are provided by the Kernel; functionality related to AI, data, and other services.

By providing a common interface to these tools, it provides the opportunity for the user code to describe the intended interaction and outcome in their code, and the Kernel is able to take care of the complexity of providing it.