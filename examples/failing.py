"""
Call into the completion and chat completion interface to test both in WASM
"""

from pydantic import BaseModel

from pharia_skill import Csi, skill


class Input(BaseModel):
    topic: str


class Output(BaseModel):
    message: str


@skill
def failing(csi: Csi, input: Input) -> Output:
    raise ValueError("I never expect to finish")
