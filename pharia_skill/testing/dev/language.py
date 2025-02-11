from pydantic import BaseModel, RootModel

from pharia_skill.csi import Language, SelectLanguageRequest


class SelectLanguageRequestSerializer(BaseModel):
    requests: list[SelectLanguageRequest]


SelectLanguageDeserializer = RootModel[list[Language | None]]
