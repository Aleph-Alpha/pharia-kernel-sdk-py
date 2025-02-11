from typing import TypeVar, Generic, Union, Optional, Protocol, Tuple, List, Any, Self
from types import TracebackType
from enum import Flag, Enum, auto
from dataclasses import dataclass
from abc import abstractmethod
import weakref

from ..types import Result, Ok, Err, Some


@dataclass
class SelectLanguageRequest:
    """
    Select the detected language for the provided input based on the list of possible languages.
    If no language matches, None is returned.
    
    text: Text input
    languages: All languages that should be considered during detection.
    """
    text: str
    languages: List[str]


def select_language(request: List[SelectLanguageRequest]) -> List[Optional[str]]:
    """
    Select most likely language from a list of supported ISO 639-3language codes.
    
    Afrikaans - "afr",
    Arabic - "ara",
    Azerbaijani - "aze",
    Belarusian - "bel",
    Bengali - "ben",
    Bosnian - "bos",
    Bulgarian - "bul",
    Catalan - "cat",
    Czech - "ces",
    Welsh - "cym",
    Danish - "dan",
    German - "deu",
    Greek - "ell",
    English - "eng",
    Esperanto - "epo",
    Estonian - "est",
    Basque - "eus",
    Persian - "fas",
    Finnish - "fin",
    French - "fra",
    Irish - "gle",
    Gujarati - "guj",
    Hebrew - "heb",
    Hindi - "hin",
    Croatian - "hrv",
    Hungarian - "hun",
    Armenian - "hye",
    Indonesian - "ind",
    Icelandic - "isl",
    Italian - "ita",
    Japanese - "jpn",
    Georgian - "kat",
    Kazakh - "kaz",
    Korean - "kor",
    Latin - "lat",
    Latvian - "lav",
    Lithuanian - "lit",
    Ganda - "lug",
    Marathi - "mar",
    Macedonian - "mkd",
    Mongolian - "mon",
    Maori - "mri",
    Malay - "msa",
    Dutch - "nld",
    Norwegian Nynorsk - "nno",
    Norwegian Bokmål - "nob",
    Punjabi - "pan",
    Polish - "pol",
    Portuguese - "por",
    Romanian - "ron",
    Russian - "rus",
    Slovak - "slk",
    Slovene - "slv",
    Shona - "sna",
    Somali - "som",
    Sotho - "sot",
    Spanish - "spa",
    Serbian - "srp",
    Albanian - "sqi",
    Swahili - "swa",
    Swedish - "swe",
    Tamil - "tam",
    Telugu - "tel",
    Tagalog - "tgl",
    Thai - "tha",
    Tswana - "tsn",
    Tsonga - "tso",
    Turkish - "tur",
    Ukrainian - "ukr",
    Urdu - "urd",
    Vietnamese - "vie",
    Xhosa - "xho",
    Yoruba - "yor",
    Chinese - "zho",
    Zulu - "zul",
    """
    raise NotImplementedError

