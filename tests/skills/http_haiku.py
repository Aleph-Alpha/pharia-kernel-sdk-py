"""
A skill that imports request, used to test that we give a good error message if Skill building fails.
"""

import requests  # noqa
from pydantic import BaseModel, RootModel

from pharia_skill import Csi, skill


class Input(RootModel[str]):
    root: str


class Output(BaseModel):
    haiku: str


@skill
def haiku(csi: Csi, input: Input) -> Output:
    return Output(haiku="Hello, world!")
