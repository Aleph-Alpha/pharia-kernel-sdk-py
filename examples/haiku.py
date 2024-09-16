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
