import json

from pharia_skill import CompletionParams, Csi, skill


@skill
def haiku(csi: Csi, input: bytes) -> bytes:
    input = json.loads(input)
    prompt = f"""Write a haiku about {input}"""
    params = CompletionParams(10, None, None, None, [])
    completion = csi.complete("llama-3.1-8b-instruct", prompt, params)
    return json.dumps(completion.text).encode()
