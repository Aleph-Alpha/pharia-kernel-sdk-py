"""
Given a search result and the full document, expand it to a larger chunk size.
"""

from pydantic import BaseModel

from pharia_skill import (
    Chunk,
    ChunkParams,
    Csi,
    Cursor,
    Document,
    DocumentPath,
    SearchResult,
    Text,
    skill,
)
from pharia_skill.testing import DevCsi


class Input(BaseModel):
    search_result: SearchResult
    document: Document


class Output(BaseModel):
    chunks: list[Chunk]


@skill
def rechunk(csi: Csi, input: Input) -> Output:
    """Return the chunks corresponding to the search result with the new size."""
    # find the corresponding content for the specified search result
    content = input.document.contents[input.search_result.start.item]
    assert isinstance(content, Text)

    # expand
    params = ChunkParams(model="pharia-1-llm-7b-control", max_tokens=20, overlap=0)
    chunks = csi.chunk(content.text, params)

    # left out further steps
    return Output(chunks=chunks)


# Start with a Search Result with old chunk size
# Retrieve the Document and the corresponding Item
# Chunk the item with the target (new) chunk size
# This could be a tokenizer if a different model is used. This means we could end up with more smaller chunks.
# Check for duplicates (two search results which were close to each other might be in one chunk after expansion).
# make sure to leave order in tact


def test_filter():
    def overlap(search_result: SearchResult, chunk: Chunk) -> bool:
        return (
            search_result.start.position <= chunk.offset < search_result.end.position
        ) or (
            chunk.offset
            < search_result.start.position
            <= chunk.offset + len(chunk.text)
        )


def test_expansion():
    # Given a search result with an unknown chunk size and the full document
    document = Document(
        path=DocumentPath(namespace="Kernel", collection="test", name="kernel/docs"),
        contents=[
            Text(
                text="You might be wondering what the Kernel is. At this point, on some level of detail, we are still in the process of figuring it out ourselves. So far, what we know is that it allows you to deploy and execute user-defined code (we call it Skills). These Skills can interact with the world using the Cognitive System Interface (CSI), which is an interface with functionality biased towards the domain of generative AI. The CSI is also the only way these skills can interact with the world. While this may seem restrictive, it facilitates a frictionless deployment experience and ensures security during execution. "
            )
        ],
        metadata={
            "created": "2025-01-01T00:00:00Z",
            "url": "https://pharia-kernel.product.pharia.com/",
        },
    )

    search_result = SearchResult(
        document_path=DocumentPath(
            namespace="Kernel", collection="test", name="kernel docs"
        ),
        content="You might be wondering what the Kernel is. At this point, on some level of detail, we are still in the process of figuring it out ourselves. So far, what we know is that it allows you to deploy and execute user-defined code (we call it Skills).",
        score=0.6931871,
        start=Cursor(item=0, position=0),
        end=Cursor(item=0, position=243),
    )

    # When "expanding" the search result to a different chunk size
    input = Input(search_result=search_result, document=document)
    output = rechunk(DevCsi(), input)

    # Expect the search result to be expanded to the larger chunk size
    assert len(output.chunks) == 9, output
