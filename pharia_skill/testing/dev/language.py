from typing import Sequence

from pydantic import RootModel

from pharia_skill.csi import Language, SelectLanguageRequest

SelectLanguageRequestSerializer = RootModel[Sequence[SelectLanguageRequest]]


SelectLanguageDeserializer = RootModel[list[Language | None]]
