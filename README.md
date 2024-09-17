# Pharia Kernel Python SDK

## Installing SDK

```shell
python -m venv .venv
source .venv/bin/activate
pip install pharia_kernel_sdk_py-0.1.0-py3-none-any.whl
```

## Developing Skills in Python

The `pharia_skill` package provides a decorator to support skill development.
The decorator inserts the Cognitive System Interface (CSI), which always need to be specified as the first argument.

```python
from pharia_skill import skill, Csi
from pharia_skill.wit.imports.csi import CompletionParams
import json


@skill
def haiku(csi: Csi, input: bytes) -> bytes:
    input = json.loads(input)
    prompt = f"""Write a haiku about {input}"""
    params = CompletionParams(10, None, None, None, [])
    completion = csi.complete("llama-3.1-8b-instruct", prompt, params)
    return json.dumps(completion.text).encode()
```

## Building skill

For packages that requires native dependency, additional wheels that is targeting WASI need to be downloaded.

### Download Pydantic WASI wheels

Supported versions:
```toml
pydantic-core = "2.14.5"
pydantic = "2.5.2"
```

Download WASI wheels:

```shell
pip install componentize-py
mkdir wasi_deps
cd wasi_deps
curl -OL https://github.com/dicej/wasi-wheels/releases/download/latest/pydantic_core-wasi.tar.gz
tar xf pydantic_core-wasi.tar.gz
```

## Contributing

Generate bindings of the skill wit world:

```shell
cd pharia_skill
rm -rf wit
componentize-py -d skill.wit -w skill bindings --world-module wit .
```

When running the examples you use `pharia_skill` without installing the wheel. You can componentize as follows:

```shell
mkdir skills
componentize-py -w skill componentize examples.haiku -o ./skills/haiku.wasm -p . -p wasi_deps
```

Then you can run `pharia-kernel` in the development directory.
