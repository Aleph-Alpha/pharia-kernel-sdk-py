from pharia_skill import Language, SelectLanguageRequest
from pharia_skill.testing.dev.language import (
    SelectLanguageDeserializer,
    SelectLanguageRequestSerializer,
)

from .conftest import dumps


def test_serialize_select_language_request():
    # Given a select language request
    request = SelectLanguageRequestSerializer(
        requests=[
            SelectLanguageRequest(
                languages=[Language.English, Language.German],
                text="What is the Kernel?",
            )
        ]
    )

    # When serializing it
    serialized = request.model_dump_json()

    # Then it nests the structure
    assert serialized == dumps(
        {
            "requests": [
                {
                    "text": "What is the Kernel?",
                    "languages": ["eng", "deu"],
                }
            ]
        }
    )


def test_deserialize_document_metadata():
    # Given a serialized select language request
    serialized = dumps(["eng", None])

    # When deserializing it
    deserialized = SelectLanguageDeserializer.model_validate_json(serialized)
    languages = deserialized.root

    # Then the languages are loaded correctly
    assert languages == [Language.English, None]
