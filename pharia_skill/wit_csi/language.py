from ..csi import Language, SelectLanguageRequest
from ..wit.imports.language import SelectLanguageRequest as WitSelectLanguageRequest


def language_to_wit(language: Language) -> str:
    return language.name


def language_from_wit(language: str) -> Language:
    try:
        return Language(language)
    except AttributeError:
        raise ValueError(f"Unsupported language: {language}")


def language_request_to_wit(request: SelectLanguageRequest) -> WitSelectLanguageRequest:
    return WitSelectLanguageRequest(
        request.text, [language_to_wit(language) for language in request.languages]
    )
