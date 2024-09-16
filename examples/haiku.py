from pharia_skill import skill
import pharia_skill.wit.imports.csi as csi
import json


@skill
def haiku(input: bytes) -> bytes:
    input = json.loads(input)
    prompt = f"""Write a haiku about {input}"""
    params = csi.CompletionParams(10, None, None, None, [])
    completion = csi.complete("llama-3.1-8b-instruct", prompt, params)
    return json.dumps(completion.text).encode()
