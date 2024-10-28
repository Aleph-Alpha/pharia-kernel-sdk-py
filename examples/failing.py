"""
Call into the completion and chat completion interface to test both in WASM
"""

from pydantic import BaseModel

from pharia_skill import Csi, skill


class Input(BaseModel):
    topic: str


@skill
def failing(csi: Csi, input: Input) -> str:
    raise ValueError("I never expect to finish")
