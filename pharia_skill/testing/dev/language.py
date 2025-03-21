from pydantic import RootModel

from pharia_skill.csi import Language, SelectLanguageRequest

SelectLanguageRequestSerializer = RootModel[list[SelectLanguageRequest]]


SelectLanguageDeserializer = RootModel[list[Language | None]]
