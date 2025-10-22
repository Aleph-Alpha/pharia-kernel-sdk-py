# FAQs

**What dependencies can I use?**

All Python-only dependencies should work, simply import them in your Skill.
For non-Python compiled dependencies ("native dependencies"), see [here](03-core_concepts.md#wasm-component).

**How do I deploy my Skill?**

Build it locally, publish it to a registry and then configure it in a [namespaces](03-core_concepts.md#namespaces).

**How is my Skill executed?**

The Engine offers a Wasm runtime in which your skill runs.
Multiple invocations of your Skill can run in parallel.
Skill Execution will be suspended after ten minutes.

**How are inference errors exposed?**

It depends. If the Engine thinks that the error might be resolved by a retry, it will do that.
In the other case, the Engine will stop the Skill Execution and return an internal server error.
