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

```python
from pharia_skill import pharia_skill as skill
import pharia_skill.skill.imports.csi as csi
import json

@skill
def haiku(input: bytes) -> bytes:
    input = json.loads(input)
    prompt = f"""Write a haiku about {input}"""
    params = csi.CompletionParams(10, None, None, None, [])
    completion = csi.complete( "llama-3.1-8b-instruct", prompt, params)
    return json.dumps(completion.text).encode()
```
