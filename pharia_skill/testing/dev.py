"""
DevCsi can be used for testing Skill code locally against a running Pharia Kernel.
"""

import os
from dataclasses import asdict

import requests
from dotenv import load_dotenv

from pharia_skill import (
    ChatParams,
    ChatResponse,
    ChunkParams,
    Completion,
    CompletionParams,
    CompletionRequest,
    Csi,
    DocumentPath,
    FinishReason,
    IndexPath,
    Language,
    Message,
    SearchResult,
)


def chat_response_from_dict(body: dict) -> "ChatResponse":
    return ChatResponse(
        message=Message(**body["message"]),
        finish_reason=FinishReason(body["finish_reason"]),
    )


class DevCsi(Csi):
    """
    DevCsi can be used for testing Skill code locally against a running Pharia Kernel.

    This implementation of Cognitive System Interface (CSI) is backed by a running instance of Pharia Kernel via HTTP.
    This enables skill developer to run and test the skill against the same services that are used by the Pharia Kernel.

    The following environment variables are required:

    * PHARIA_KERNEL_ADDRESS (Pharia Kernel endpoint; example: "https://pharia-kernel.aleph-alpha.stackit.run")
    * AA_API_TOKEN (Aleph Alpha API token)
    """

    VERSION = "0.2"

    def __init__(self):
        load_dotenv()
        self.url = os.environ["PHARIA_KERNEL_ADDRESS"] + "/csi"
        token = os.environ["AA_API_TOKEN"]
        self.session = requests.Session()
        self.session.headers = {"Authorization": f"Bearer {token}"}

    def __del__(self):
        if hasattr(self, "session"):
            self.session.close()

    def complete(self, model: str, prompt: str, params: CompletionParams) -> Completion:
        data = {
            "version": self.VERSION,
            "function": self.complete.__name__,
            "prompt": prompt,
            "model": model,
            "params": asdict(params),
        }
        response = self.session.post(self.url, json=data)
        if response.status_code != 200:
            raise Exception(f"{response.status_code}: {response.text}")
        return Completion(**response.json())

    def chunk(self, text: str, params: ChunkParams) -> list[str]:
        data = {
            "version": self.VERSION,
            "function": self.chunk.__name__,
            "text": text,
            "params": asdict(params),
        }
        response = self.session.post(self.url, json=data)
        if response.status_code != 200:
            raise Exception(f"{response.status_code}: {response.text}")
        return response.json()

    def chat(
        self, model: str, messages: list[Message], params: ChatParams
    ) -> ChatResponse:
        data = {
            "version": self.VERSION,
            "function": self.chat.__name__,
            "model": model,
            "messages": [asdict(m) for m in messages],
            "params": asdict(params),
        }
        response = self.session.post(self.url, json=data)
        if response.status_code != 200:
            raise Exception(f"{response.status_code}: {response.text}")
        return chat_response_from_dict(response.json())

    def select_language(self, text: str, languages: list[Language]) -> Language | None:
        data = {
            "version": self.VERSION,
            "function": self.select_language.__name__,
            "text": text,
            "languages": [language.name.lower() for language in languages],
        }
        response = self.session.post(self.url, json=data)
        if response.status_code != 200:
            raise Exception(f"{response.status_code}: {response.text}")
        match response.json():
            case "eng":
                return Language.ENG
            case "deu":
                return Language.DEU
            case _:
                return None

    def complete_all(self, requests: list[CompletionRequest]) -> list[Completion]:
        data = {
            "version": self.VERSION,
            "function": self.complete_all.__name__,
            "requests": [asdict(request) for request in requests],
        }
        response = self.session.post(self.url, json=data)
        if response.status_code != 200:
            raise Exception(f"{response.status_code}: {response.text}")
        return [Completion(**completion) for completion in response.json()]

    def search(
        self,
        index_path: IndexPath,
        query: str,
        max_results: int = 1,
        min_score: float | None = None,
    ) -> list[SearchResult]:
        data = {
            "version": self.VERSION,
            "function": self.search.__name__,
            "index_path": asdict(index_path),
            "query": query,
            "max_results": max_results,
            "min_score": min_score,
        }
        response = self.session.post(self.url, json=data)
        if response.status_code != 200:
            raise Exception(f"{response.status_code}: {response.text}")
        return [
            SearchResult(
                document_path=DocumentPath(**result["document_path"]),
                content=result["content"],
                score=result["score"],
            )
            for result in response.json()
        ]
