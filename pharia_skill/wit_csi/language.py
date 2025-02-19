from ..csi import Language, SelectLanguageRequest
from ..wit.imports import language as wit


def language_to_wit(language: Language) -> str:
    return language.name


def language_from_wit(language: str) -> Language:
    try:
        return Language(language)
    except AttributeError:
        raise ValueError(f"Unsupported language: {language}")


def language_request_to_wit(
    request: SelectLanguageRequest,
) -> wit.SelectLanguageRequest:
    return wit.SelectLanguageRequest(
        request.text, [language_to_wit(language) for language in request.languages]
    )
