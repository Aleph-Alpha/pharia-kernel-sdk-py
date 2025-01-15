"""
Test document search and metadata in WASM
"""

from pydantic import BaseModel, RootModel

from pharia_skill import Csi, skill
from pharia_skill.csi import IndexPath


class Input(RootModel[str]):
    root: str


class Output(RootModel[str | None]):
    root: str | None


class Metadata(BaseModel):
    url: str


@skill
def haiku(csi: Csi, input: Input) -> Output:
    index_path = IndexPath("Kernel", "test", "asym-64")
    search_results = csi.search(index_path=index_path, query=input.root, max_results=1)
    if not search_results:
        return Output(root=None)

    # parse into list of Metadata
    results = csi.document_metadata(search_results[0].document_path)
    if not isinstance(results, list):
        return Output(root=None)

    metadata = [Metadata(**result) for result in results]
    return Output(root=metadata[0].url)
