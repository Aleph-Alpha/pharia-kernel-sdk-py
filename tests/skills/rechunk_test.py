"""
Given a search result and the full document, expand it to a larger chunk size.
"""

import pytest
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
    """The skill input

    Attributes:
        search_result  The search result within the same item in the specified document.
        document       The original document.
    """

    search_result: SearchResult
    document: Document


class Output(BaseModel):
    """The skill output

    Attributes:
        chunks  The list of relevant document chunks that overlap with the search results.
    """

    chunks: list[Chunk]


def overlap(search_result: SearchResult, chunk: Chunk) -> bool:
    """Check if the specified chunk overlaps with the search result."""
    return max(search_result.start.position, chunk.character_offset) <= min(
        search_result.end.position, chunk.character_offset + len(chunk.text)
    )


def filter(search_result: SearchResult, chunks: list[Chunk]) -> list[Chunk]:
    """Filter for chunks that overlap with the specified search result."""
    return [chunk for chunk in chunks if overlap(search_result, chunk)]


@skill
def rechunk(csi: Csi, input: Input) -> Output:
    """Return the chunks corresponding to the search result with the new size."""
    # find the corresponding content for the specified search result
    content = input.document.contents[input.search_result.start.item]
    assert isinstance(content, Text)

    # expand
    params = ChunkParams(model="llama-3.1-8b-instruct", max_tokens=20, overlap=0)
    chunks = csi.chunk(content.text, params)

    # filter
    relevant_chunks = filter(input.search_result, chunks)

    # left out further steps
    return Output(chunks=relevant_chunks)


@pytest.mark.kernel
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
    assert len(output.chunks) == 5, output
