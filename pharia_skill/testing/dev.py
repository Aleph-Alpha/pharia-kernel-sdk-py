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
    IndexPath,
    Language,
    Message,
    Role,
    SearchResult,
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
        role_to_str = {
            Role.USER: "User",
            Role.SYSTEM: "System",
            Role.ASSISTANT: "Assistant",
        }
        role_from_str = {
            "User": Role.USER,
            "System": Role.SYSTEM,
            "Assistant": Role.ASSISTANT,
        }
        data = {
            "version": self.VERSION,
            "function": self.chat.__name__,
            "model": model,
            "messages": [
                {"role": role_to_str[m.role], "content": m.content} for m in messages
            ],
            "params": asdict(params),
        }
        response = self.session.post(self.url, json=data)
        if response.status_code != 200:
            raise Exception(f"{response.status_code}: {response.text}")
        res_body = response.json()
        msg = res_body["message"]
        finish_reason = res_body["finish_reason"]
        return ChatResponse(
            message=Message(role=role_from_str[msg["role"]], content=msg["content"]),
            finish_reason=finish_reason,
        )

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
