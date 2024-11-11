"""
Call into the completion and chat completion interface to test both in WASM
"""

from pydantic import RootModel

from pharia_skill import Csi, skill

Input = RootModel[str]
Output = RootModel[str]


@skill
def failing(csi: Csi, input: Input) -> Output:
    raise ValueError("I never expect to finish")
