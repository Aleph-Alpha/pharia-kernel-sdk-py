"""
DevCsi can be used for testing Skill code locally against a running Pharia Kernel.
"""

import os
from dataclasses import asdict

import requests
from dotenv import load_dotenv

from ..csi import (
    ChunkParams,
    Completion,
    CompletionParams,
    CompletionRequest,
    Csi,
    Language,
)


class _DevCsi(Csi):
    VERSION = "v0_2"

    def __init__(self):
        load_dotenv()
        self.url = os.environ["PHARIA_KERNEL_CSI_ADDRESS"] + "/csi"
        token = os.environ["AA_API_TOKEN"]
        self.session = requests.Session()
        self.session.headers = {"Authorization": f"Bearer {token}"}

    def __del__(self):
        self.session.close()

    def complete(
        self, model: str, prompt: str, params: CompletionParams
    ) -> Completion:
        data = {
            "version": self.VERSION,
            "function": self.complete.__name__,
            "prompt": prompt,
            "model": model,
            "params": asdict(params),
        }
        response = self.session.post(self.url, json=data)
        response.raise_for_status()
        return Completion(**response.json())

    def chunk(self, text: str, params: ChunkParams) -> list[str]:
        data = {
            "version": self.VERSION,
            "function": self.chunk.__name__,
            "text": text,
            "params": asdict(params),
        }
        response = self.session.post(self.url, json=data)
        response.raise_for_status()
        return response.json()

    def select_language(
        self, text: str, languages: list[Language]
    ) -> Language | None:
        data = {
            "version": self.VERSION,
            "function": self.select_language.__name__,
            "text": text,
            "languages": [language.name.lower() for language in languages],
        }
        response = self.session.post(self.url, json=data)
        response.raise_for_status()
        match response.json():
            case "eng":
                return Language.ENG
            case "deu":
                return Language.DEU
            case _:
                return None

    def complete_all(
        self, requests: list[CompletionRequest]
    ) -> list[Completion]:
        data = {
            "version": self.VERSION,
            "function": self.complete_all.__name__,
            "requests": [asdict(request) for request in requests],
        }
        response = self.session.post(self.url, json=data)
        response.raise_for_status()
        return [Completion(**completion) for completion in response.json()]
