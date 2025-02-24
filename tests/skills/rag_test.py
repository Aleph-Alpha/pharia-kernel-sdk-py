"""
Given a search result and the full document, expand it to a larger chunk size.
"""

from pydantic import BaseModel

from pharia_skill import ChunkParams, Csi, skill
from pharia_skill.testing import DevCsi


class Input(BaseModel):
    search_result: str
    document: str


class Output(BaseModel):
    chunks: list[str]


@skill
def rag_expand_only(csi: Csi, input: Input) -> Output:
    # left out in this example: find occurrence

    # expand
    params = ChunkParams(model="pharia-1-llm-7b-control", max_tokens=20, overlap=0)
    chunks = csi.chunk(input.document, params)

    # left out further steps
    return Output(chunks=chunks)


# Start with a Search Result with old chunk size
# Retrieve the Document and the corresponding Item
# Chunk the item with the target (new) chunk size
# This could be a tokenizer if a different model is used. This means we could end up with more smaller chunks.
# Check for duplicates (two search results which were close to each other might be in one chunk after expansion).
# make sure to leave order in tact


def test_expansion():
    # Given a search result with an unknown chunk size and the full document
    document = "You might be wondering what the Kernel is. At this point, on some level of detail, we are still in the process of figuring it out ourselves. So far, what we know is that it allows you to deploy and execute user-defined code (we call it Skills). These Skills can interact with the world using the Cognitive System Interface (CSI), which is an interface with functionality biased towards the domain of generative AI. The CSI is also the only way these skills can interact with the world. While this may seem restrictive, it facilitates a frictionless deployment experience and ensures security during execution. "

    search_result = "You might be wondering what the Kernel is. At this point, on some level of detail, we are still in the process of figuring it out ourselves. So far, what we know is that it allows you to deploy and execute user-defined code (we call it Skills)."

    # When "expanding" the search result to a different chunk size
    input = Input(search_result=search_result, document=document)
    output = rag_expand_only(DevCsi(), input)

    # Expect the search result to be expanded to the larger chunk size
    assert len(output.chunks) == 9, output
