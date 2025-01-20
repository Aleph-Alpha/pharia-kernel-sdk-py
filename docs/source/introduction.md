# Introduction

Frameworks like `llama-stack` and `langchain` allow for quick prototyping of generative AI applications. However, building production-ready AI applications requires solving different challenges. Companies do not want to compromize on security, testability, traceability, and evaluation of their AI logic.

## What Problem does the Kernel solve?

Most PoCs that develop AI methodology using a Python framework wrap it in a webserver and containerize it. But this means that each piece of AI logic comes with its own set of libraries, dependencies and webserver. These dependencies need to be kept up to date. Each deployment needs to make decisions on how to do tracing, how to authenticate users and how to solve scaling. Maintaining, updating and synchronizing these containers quickly becomes resource intensive.

This is the problem the Kernel solves. The Kernel provides a constrained, but capable interface each Skill can interact with.
Complexity like authentication, tracing and scaling is abstracted away behind this interface. The Skill developer can focus on methodology development.

## Unique Selling Points

As outlined above, it is fairly easy to put together PoC AI Skills. Such PoCs are often a security-risk, lack scalability and will become a maintenance nightmare.

The Kernel comes with several Unique Selling Points that makes it the system of choice for deploying hundreds of AI Skills in a secure, scalable and maintainable way:

### Speed of Deployment

The Kernel allows developers to focus on the problems they are trying to solve. It abstracts away most of the complexity of deploying AI applications.
Once developers are happy with their methodology, a new or updated Skill can be brought into production within seconds.

### Scalability

Skills in the Kernel run as serverless components. This means your code can serve many requests in parallel. Long, blocking calls to inference which often
become a problem in AI applications do not prevent your Skill from being accessible.

Serverless components also mean that you do not need to worry about uptime and scaling, as the Kernel will allocate resources dynamically between Skills.

### Maintainability

You do not need to bring dependencies that take care of protocols like HTTP or file standards, as the Kernel already provides these capabilities.
Less dependencies mean less maintenance burden to keep dependencies up to date.

### Security

AI applications become most useful when they have access to your knowledge base.
This is also when they become a security risk, as this knowledge must not be exposed to unauthorized persons.
The Kernel restricts the way that Skills can interact with the outside world. 
This allows developers to be creative in their methodology while minimizing the attack surface.

### Compliance

The Kernel exposes some configuration options that can be set centrally for all Skills.
This means that all of your skills operate in the same way.
Metrics, telemetry, authentication and inference backend do not need to be specified per Skill.

### Deployment

Skill management and deployment follows modern best practices. Skills can be stored in and loaded from any configured OCI registry.

### Integration into PhariaAI

The Kernel integrates tightly into the PhariaAI stack. Traces can be viewed in PhariaStudio and Skills can be evaluated against uploaded datasets.

### Discoverability

The Kernel makes it easy to retrieve descriptions and metadata like input and output schema for Skills.

### Agent Ready

The more autonomy and control AI Skills become, the more important it becomes that they run in a constrained environment in which every interaction
with the outside world can be traced and maintained. The Kernel already supports basic building blocks that are needed to have fully autonomous agents
and will support agent workloads in the future.