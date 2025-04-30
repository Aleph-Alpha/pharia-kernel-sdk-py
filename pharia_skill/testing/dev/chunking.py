from typing import Sequence

from pydantic import RootModel

from pharia_skill.csi import Chunk, ChunkRequest

ChunkRequestSerializer = RootModel[Sequence[ChunkRequest]]


ChunkDeserializer = RootModel[list[list[Chunk]]]
