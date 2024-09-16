# Pharia Kernel Python SDK

## Cheatsheet

```shell
python -m venv .venv
source .venv/bin/activate
pip install componentize-py
pip install pharia_kernel_sdk_py-0.1.0-py3-none-any.whl
# ...  develop skill code in e.g. haiku.py ...
componentize-py -w skill componentize haiku -o ./haiku.wasm
```

## Developing Skills in Python

The `pharia_skill` package provides a decorator to support skill development.
The decorator inserts the Cognitive System Interface (CSI), which always need to be specified as the first argument.

```python
from pharia_skill import skill
import json


@skill
def haiku(csi, input: bytes) -> bytes:
    input = json.loads(input)
    prompt = f"""Write a haiku about {input}"""
    params = csi.CompletionParams(10, None, None, None, [])
    completion = csi.complete("llama-3.1-8b-instruct", prompt, params)
    return json.dumps(completion.text).encode()
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
componentize-py -w skill componentize examples.haiku -o ./skills/haiku.wasm
```

Then you can run `pharia-kernel` in the development directory.
