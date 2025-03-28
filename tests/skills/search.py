"""
Test document search and metadata in WASM
"""

from pydantic import RootModel

from pharia_skill import Csi, Document, IndexPath, skill


class Input(RootModel[str]):
    root: str


class Output(RootModel[str | None]):
    root: str | None


@skill
def search(csi: Csi, input: Input) -> Output:
    index_path = IndexPath("Kernel", "test", "asym-64")
    search_results = csi.search(index_path=index_path, query=input.root, max_results=1)
    assert search_results

    # retrieve document
    document = csi.document(search_results[0].document_path)
    assert isinstance(document, Document)
    assert document.path == search_results[0].document_path
    assert document.text.startswith("You might be wondering")

    # parse into list of Metadata
    result = csi.document_metadata(search_results[0].document_path)
    assert isinstance(result, dict)
    return Output(root=result["url"])
