# Pharia Kernel Python SDK

You build your skill in Python, which is then compiled into a Wasm module.
Then, the skill is deployed to an [instance of Pharia Kernel](https://pharia-kernel.product.pharia.com),
where it can be invoked on demand.
To this end, this SDK provides some tooling and APIs for skill development.

You can access the [Documentation](https://aleph-alpha-pharia-kernel-sdk-py.readthedocs-hosted.com/en/latest/index.html)
with your GitHub account.

## Installing the SDK

While we are planning to open source the SDK soon, it is currently distributed via the Aleph Alpha Artifactory PyPI.
To install it, you need a JFrog account and need to create an access token in the UI.
We recommend using [uv](https://docs.astral.sh/uv/) to install the SDK.

To add the SDK as a dependency to an existing project managed by `uv`, first create a `.env` file and set the needed environment variables:

```sh
# .env
UV_INDEX_JFROG_USERNAME=your-username
UV_INDEX_JFROG_PASSWORD=$JFROG_TOKEN
```

Then, add the SDK as a dependency:

```sh
set -a && source .env
uv add --index jfrog=https://alephalpha.jfrog.io/artifactory/api/pypi/python/simple pharia-kernel-sdk-py
```

## Contributing

Install the dependencies with

```shell
uv sync --dev
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