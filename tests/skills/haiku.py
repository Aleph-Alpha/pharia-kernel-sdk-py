"""
Call into the completion and chat completion interface to test both in Wasm
"""

from pydantic import BaseModel, RootModel

from pharia_skill import ChatParams, CompletionParams, Csi, Message, skill


class Input(RootModel[str]):
    root: str


class Output(BaseModel):
    completion: str
    completion_special_tokens: str
    chat: str


@skill
def haiku(csi: Csi, input: Input) -> Output:
    """We do a completion and chat request in the same skill to test both."""
    prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

    You are a poet who strictly speaks in haikus.<|eot_id|><|start_header_id|>user<|end_header_id|>

    {input.root}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""
    params = CompletionParams(max_tokens=64)
    completion = csi.complete("llama-3.1-8b-instruct", prompt, params)

    # same prompt as above but for the chat completion
    msg = Message.user(f"You are a poet who strictly speaks in haikus.\n\n{input.root}")
    chat_completion = csi.chat(
        "llama-3.1-8b-instruct", [msg], ChatParams(max_tokens=64)
    )
    params = CompletionParams(max_tokens=64, return_special_tokens=True)
    completion_special_tokens = csi.complete("llama-3.1-8b-instruct", prompt, params)
    return Output(
        completion=completion.text.strip(),
        completion_special_tokens=completion_special_tokens.text.strip(),
        chat=chat_completion.message.content.strip(),
    )
