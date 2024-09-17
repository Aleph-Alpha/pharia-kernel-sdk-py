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
from pydantic import BaseModel

from pharia_skill import CompletionParams, Csi, skill


class Input(BaseModel):
    topic: str


@skill
def haiku(csi: Csi, input: Input) -> str:
    prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

    You are a poet who strictly speaks in haikus.<|eot_id|><|start_header_id|>user<|end_header_id|>

    {input.topic}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""
    params = CompletionParams(10, None, None, None, [])
    completion = csi.complete("llama-3.1-8b-instruct", prompt, params)
    return completion.text.strip()
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
cd ..
```

## Contributing

Generate bindings of the skill wit world:

```shell
cd pharia_skill
rm -rf wit
componentize-py -d skill.wit -w skill bindings --world-module wit .
cd ..
```

When running the examples you use `pharia_skill` without installing the wheel. You can componentize as follows:

```shell
mkdir skills
componentize-py -w skill componentize examples.haiku -o ./skills/haiku.wasm -p . -p wasi_deps
```

Then you can run `pharia-kernel` in the development directory.
