from pydantic import BaseModel

from pharia_skill import CompletionParams, Csi, skill


class MyModel(BaseModel):
    topic: str


@skill
def haiku(csi: Csi, input: MyModel) -> str:
    prompt = f"""Write a haiku about {input.topic}"""
    params = CompletionParams(10, None, None, None, [])
    completion = csi.complete("llama-3.1-8b-instruct", prompt, params)
    return completion.text
