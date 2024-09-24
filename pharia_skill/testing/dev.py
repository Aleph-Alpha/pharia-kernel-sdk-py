"""
DevCsi can be used for testing Skill code locally against a running Pharia Kernel.
"""

import os
from dataclasses import asdict

import requests

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

    def complete(self, model: str, prompt: str, params: CompletionParams) -> Completion:
        data = {
            "version": self.VERSION,
            "function": self.complete.__name__,
            "prompt": prompt,
            "model": model,
            "params": asdict(params),
        }
        url = os.environ["PHARIA_KERNEL_ADDRESS"]
        token = os.environ["AA_API_TOKEN"]
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        return Completion(**response.json())

    def chunk(self, text: str, params: ChunkParams) -> list[str]:
        raise NotImplementedError

    def select_language(self, text: str, languages: list[Language]) -> Language | None:
        raise NotImplementedError

    def complete_all(self, requests: list[CompletionRequest]) -> list[Completion]:
        raise NotImplementedError
