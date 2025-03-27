# Pharia Kernel Python SDK

You build your skill in Python, which is then compiled into a Wasm module.
Then, the skill is deployed to an [instance of Pharia Kernel](https://pharia-kernel.product.pharia.com),
where it can be invoked on demand.
To this end, this SDK provides some tooling and APIs for skill development.

You can access the [Documentation](https://pharia-skill.readthedocs.io) on readthedocs.

## Installing the SDK

The SDK is published on PyPi.
We recommend using [uv](https://docs.astral.sh/uv/) to manage Python dependencies.
To add the SDK as a dependency to an existing project managed by `uv`, run

```sh
uv add pharia-skill
```

## Contributing

Install the dependencies with

```shell
uv sync --dev --frozen
```

We use [pre-commit](https://pre-commit.com/) to check that code is formatted, linted and type checked. You can initialize by simply typing

```shell
pre-commit
pre-commit install
```

Verify that it is running with

```shell
pre-commit run --all-files
```
