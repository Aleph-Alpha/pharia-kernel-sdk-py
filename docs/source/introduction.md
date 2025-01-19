# Introduction

Frameworks like `llama-stack` and `langchain` allow for quick prototyping of generative AI applications. However, building production-ready AI applications requires solving different challenges. Companies do not want to compromize on security, testability, traceability, and evaluation of their AI logic.

```{image} ../../_static/exhausted.png
:alt: Exhausted Sloth
:width: 200px
```

## What Problem does the Kernel solve?

Most PoCs that develop AI methodology using a Python framework wrap it in a webserver and containerize it. But this means that each piece of AI logic comes with its own set of libraries, dependencies and webserver. These dependencies need to be kept up to date. Each deployment needs to make decisions on how to do tracing, how to authenticate users and how to solve scaling. Maintaining, updating and synchronizing these containers quickly becomes resource intensive.

This is the problem the Kernel solves. The Kernel provides a constrained, but capable interface each skill can interact with.
Complexity like authentication, tracing and scaling is abstracted away behind this interfaces. The skill developer can focus on methodology development.

## Unique Selling Points

As outlined above, it is fairly easy to put together PoC AI skills. Such PoCs are often a security-risk, lack scalability and will become a maintenance nightmare.

The Kernel comes with several Unique Selling Points that makes it the system of choice for deploying hundreds of AI skills in a secure, scalable and maintainable way:

### Speed of Deployment

The Kernel allows developers to focus on the problems they are trying to solve. It abstracts away most of the accidental complexity of deploying AI applications.
Once developers are happy with their methodology, a new or updated skill can be brought into production within seconds.

### Scalability

Skills in the Kernel run as serverless components. There is no limit on the parallel requests that the Kernel can process. Long, blocking calls to inference which often
become a problem in AI applications do not prevent your skill from being accessible. You don't need to monitor hundreds of containers and worry about uptime. Your skill is always available.

### Maintainability

While you can include dependency libraries into your skill, a skill is itself does not need to worry about protocols like HTTP or file standard.
This means there less maintenance burden to update dependencies and adapt to changes in HTTP frameworks.

### Security

AI applications become most useful when they have access to your knowledge base.
This is also when they become a security risk, as this knowledge must not be exposed to unauthorized persons.
The Kernels restricts the way that skills can interact with the outside world. 
This allows developers to be creative in their methodology while minimizing the attack surface.

### Central Configuration

Do you want to switch your telemetry backend or update the way your skill is traced? Update the setting on the Kernel and all your traces will go to a different place.

### GitOps

Skill management and deployment follows modern best practices. Skills can be scored in arbitrary registries from which the Kernel loads them.

### Integration

The Kernel integrates tightly into the Pharia stack. Traces can be viewed in the PhariaStudio and skills can be evaluated against uploaded datasets.

### Discoverability

The Kernel provides a skill catalogue that makes it easy to retrieve descriptions and metadata like input and output schema for skills.

### Agent Ready

The more autonomy and control AI skills become, the more important it becomes that they run in a constrained environment in which every interaction
with the outside world can be traced and maintained. The Kernel already supports basic building blocks that are needed to have fully autonomous agents
and will support agent workloads in the future.