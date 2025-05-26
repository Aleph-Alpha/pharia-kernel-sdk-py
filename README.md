# Pharia Kernel Python SDK

You build your skill in Python, which is then compiled into a Wasm module.
Then, the skill is deployed to an [instance of Pharia Kernel](https://pharia-kernel.product.pharia.com),
where it can be invoked on demand.
To this end, this SDK provides the tooling and APIs for skill development.

You can access the documentation on [Read the Docs](https://pharia-skill.readthedocs.io).

## Installing the SDK

The SDK is published on [PyPI](https://pypi.org/project/pharia-skill/).
We recommend using [uv](https://docs.astral.sh/uv/) to manage Python dependencies.

To add the SDK as a dependency to an existing project managed by `uv`, run

```sh
uv add pharia-skill
```

In case you want to use changes in the SDK that have not been released, use GitHub as source:

```sh
uv add git+https://github.com/aleph-alpha/pharia-kernel-sdk-py.git
```