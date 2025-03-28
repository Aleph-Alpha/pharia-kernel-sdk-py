"""
Call into the language detection interface to test it in WASM
"""

from pydantic import BaseModel, RootModel

from pharia_skill import Csi, Language, skill


class Input(RootModel[str]):
    root: str


class Output(BaseModel):
    language: str | None


@skill
def language(csi: Csi, input: Input) -> Output:
    lang = csi.select_language(input.root, list(Language))

    return Output(language=lang.value if lang else None)
