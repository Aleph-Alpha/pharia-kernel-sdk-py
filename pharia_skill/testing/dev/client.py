"""
Make HTTP requests against a running Pharia Kernel.

By separating the client from the `DevCsi`, we can better test the serialization/deserialization
and other functionality of the `DevCsi` without making HTTP requests.
"""

import os
from http import HTTPStatus
from typing import Any, Generator, Protocol

import requests
from dotenv import load_dotenv
from sseclient import Event, SSEClient


class CsiClient(Protocol):
    def run(self, function: str, data: dict[str, Any]) -> Any: ...
    def stream(
        self, function: str, data: dict[str, Any]
    ) -> Generator[Event, None, None]: ...


class Client(CsiClient):
    """Make requests with a given payload against a running Pharia Kernel."""

    HTTP_CSI_VERSION = "v1"

    def __init__(self) -> None:
        """Create a new HTTP client.

        The session is stored to allow for re-use of the same connection between tests.
        """
        load_dotenv()
        self.url = (
            f"""{os.environ["PHARIA_KERNEL_ADDRESS"]}/csi/{self.HTTP_CSI_VERSION}"""
        )
        token = os.environ["PHARIA_AI_TOKEN"]
        self.session = requests.Session()
        self.session.headers = {
            "Authorization": f"Bearer {token}",
        }

    def __del__(self) -> None:
        if hasattr(self, "session"):
            self.session.close()

    def run(self, function: str, data: Any) -> Any:
        url = f"{self.url}/{function}"
        response = self.session.post(
            url,
            json=data,
        )
        # Always forward the error message from the kernel
        if response.status_code >= 400:
            try:
                error = response.json()
            except requests.JSONDecodeError:
                error = response.text
            raise Exception(
                f"{response.status_code} {HTTPStatus(response.status_code).phrase}: {error}"
            )

        return response.json()

    def stream(
        self, function: str, data: dict[str, Any]
    ) -> Generator[Event, None, None]:
        url = f"{self.url}/{function}"
        headers = {"Accept": "text/event-stream", **self.session.headers}
        response = self.session.post(url, json=data, headers=headers, stream=True)
        # Always forward the error message from the kernel
        if response.status_code >= 400:
            try:
                error = response.json()
            except requests.JSONDecodeError:
                error = response.text
            raise Exception(
                f"{response.status_code} {HTTPStatus(response.status_code).phrase}: {error}"
            )

        return SSEClient(response).events()  # type: ignore
