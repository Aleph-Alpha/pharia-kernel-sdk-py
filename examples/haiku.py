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
