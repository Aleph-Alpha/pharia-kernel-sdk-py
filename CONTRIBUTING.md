# Contributing

Generate bindings of the skill wit world:

```shell
cd pharia_skill
rm -rf bindings
componentize-py -d wit -w skill bindings --world-module bindings .
cd ..
```

To generate bindings with all unstable feature, replace the third command with

```shell
componentize-py --all-features -d wit -w skill bindings --world-module bindings .
```

When running the examples, you use `pharia_skill` without installing the wheel. You can componentize as follows:

```shell
mkdir skills
componentize-py -w skill componentize examples.haiku -o ./skills/haiku.wasm -p . -p wasi_deps
```

Then you can run `pharia-kernel` in the development directory.

## Unstable Features

When generating bindings for unstable features, we must not use these bindings in the library until they are stabilized.
Otherwise, we will break builds that do not have the `unstable` flag.
One example is that type annotations of unstable records in the `wit_csi` module must be put in parenthesis.