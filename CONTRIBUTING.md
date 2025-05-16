# Contributing

## Install dependencies

```shell
uv sync --dev --extra cli --frozen
```

## Running `pre-commit` hooks

We use [pre-commit](https://pre-commit.com/) to check that code is formatted, linted and type checked. You can initialize by simply typing

```shell
pre-commit
pre-commit install
```

Verify that it is running with

```shell
pre-commit run --all-files
```

## Generating WIT bindings

Generate the bindings of the Skill WIT world:

```shell
cd pharia_skill
rm -rf bindings
componentize-py -d wit -w skill-all bindings --world-module bindings .
cd ..
```

### Unstable Features

To generate bindings with all unstable feature, replace the third command with

```shell
componentize-py --all-features -d wit -w skill-all bindings --world-module bindings .
```

When generating bindings for unstable features, we must not use these bindings in the library until they are stabilized.
Otherwise, we will break builds that do not have the `unstable` flag.
One example is that type annotations of unstable records in the `wit_csi` module must be put in quotes.
