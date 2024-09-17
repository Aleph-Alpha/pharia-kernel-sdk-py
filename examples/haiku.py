import json

from pharia_skill import CompletionParams, Csi, skill
from pydantic import BaseModel


class MyModel(BaseModel):
    topic: str


@skill
def haiku(csi: Csi, input: bytes) -> bytes:
    topic = MyModel.model_validate_json(input).topic
    prompt = f"""Write a haiku about {topic}"""
    params = CompletionParams(10, None, None, None, [])
    completion = csi.complete("llama-3.1-8b-instruct", prompt, params)
    return json.dumps(completion.text).encode()
