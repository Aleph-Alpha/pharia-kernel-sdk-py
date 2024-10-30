"""
Call into the completion and chat completion interface to test both in WASM
"""

from pydantic import BaseModel

from pharia_skill import ChatParams, CompletionParams, Csi, Message, skill


class Input(BaseModel):
    topic: str


@skill
def haiku(
    csi: Csi, input: Input, model: str = "llama-3.1-8b-instruct"
) -> dict[str, str]:
    prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

    You are a poet who strictly speaks in haikus.<|eot_id|><|start_header_id|>user<|end_header_id|>

    {input.topic}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""
    params = CompletionParams(max_tokens=64)
    completion = csi.complete(model, prompt, params)

    # same prompt as above but for the chat completion
    msg = Message.user(
        f"You are a poet who strictly speaks in haikus.\n\n{input.topic}"
    )
    chat_completion = csi.chat(model, [msg], ChatParams(max_tokens=64))
    return {
        "completion": completion.text.strip(),
        "chat": chat_completion.message.content.strip(),
    }
