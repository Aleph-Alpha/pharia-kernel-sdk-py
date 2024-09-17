from pydantic import BaseModel

from pharia_skill import CompletionParams, Csi, skill


class Input(BaseModel):
    topic: str


@skill
def haiku(csi: Csi, input: Input) -> str:
    prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

    You are a poet who strictly speaks in haikus.<|eot_id|><|start_header_id|>user<|end_header_id|>

    {input.topic}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""
    params = CompletionParams(max_tokens=64)
    completion = csi.complete("llama-3.1-8b-instruct", prompt, params)
    return completion.text.strip()
