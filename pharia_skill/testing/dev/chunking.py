from pydantic import BaseModel, RootModel

from pharia_skill.csi import ChunkRequest


class ChunkRequestSerializer(BaseModel):
    requests: list[ChunkRequest]


ChunkDeserializer = RootModel[list[list[str]]]
