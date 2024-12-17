"""
Test document search and metadata in WASM
"""

from typing import cast

from pydantic import RootModel

from pharia_skill import Csi, skill
from pharia_skill.csi import IndexPath


class Input(RootModel):
    root: str


class Output(RootModel):
    root: str | None


@skill
def haiku(csi: Csi, input: Input) -> Output:
    index_path = IndexPath("Kernel", "test", "asym-64")
    results = csi.search(index_path=index_path, query=input.root, max_results=1)
    if not results:
        return Output(root=None)
    metadata = cast(list[dict] | None, csi._document_metadata(results[0].document_path))
    if not metadata:
        return Output(root=None)
    return Output(root=metadata[0]["url"])
