"""
Call into the completion and chat completion interface to test both in WASM
"""

from pydantic import RootModel

from pharia_skill import Csi, skill


class Input(RootModel):
    root: str


class Output(RootModel):
    root: str


@skill
def failing(csi: Csi, input: Input) -> Output:
    raise ValueError("I never expect to finish")
