from ..bindings.imports import language as wit
from ..csi import Language, SelectLanguageRequest


def language_to_wit(language: Language) -> str:
    return language.value


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
