from pydantic import RootModel

from pharia_skill.csi import Chunk, ChunkRequest

ChunkRequestSerializer = RootModel[list[ChunkRequest]]


ChunkDeserializer = RootModel[list[list[Chunk]]]
