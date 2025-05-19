"""
A Skill that calls into the CSI with a wrong type (e.g. None for the model name which is a string).

Passing bad types to componentize-py raises very hard to understand errors.
This skill is used as part of an integration test to ensure that we catch these errors early.
"""

from pydantic import BaseModel, RootModel

from pharia_skill import CompletionParams, Csi, skill


class Input(RootModel[str]):
    root: str


class Output(BaseModel):
    completion: str


@skill
def bad_csi_input(csi: Csi, input: Input) -> Output:
    params = CompletionParams(max_tokens=64)
    model = None
    completion = csi.complete(model, "Hello", params)  # type: ignore
    return Output(
        completion=completion.text.strip(),
    )
