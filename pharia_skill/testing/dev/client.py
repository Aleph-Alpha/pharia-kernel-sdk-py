"""
Make HTTP requests against a running Pharia Kernel.

By separating the client from the `DevCsi`, we can better test the serialization/deserialization
and other functionality of the `DevCsi` without making HTTP requests.
"""

import json
import os
from http import HTTPStatus
from typing import Any, Generator, Protocol

import requests
from dotenv import load_dotenv
from pydantic import BaseModel


class Event(BaseModel):
    event: str
    data: dict[str, Any]


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

        return KernelStreamDeserializer(response).events()


class KernelStreamDeserializer:
    def __init__(self, response: requests.Response) -> None:
        self.response = response

    def _read(self) -> Generator[bytes, None, None]:
        """Read the incoming event source stream and yield event chunks.

        Unfortunately it is possible for some servers to decide to break an
        event into multiple HTTP chunks in the response. It is thus necessary
        to correctly stitch together consecutive response chunks and find the
        SSE delimiter (empty new line) to yield full, correct event chunks."""
        data = b""
        for chunk in self.response:
            for line in chunk.splitlines(True):
                data += line
                if data.endswith((b"\r\r", b"\n\n", b"\r\n\r\n")):
                    yield data
                    data = b""
        if data:
            yield data

    def events(self) -> Generator[Event, None, None]:
        """Yield events from the kernel stream.

        This method does not raise on error events, but rather deserializes them and
        leaves it to the caller to raise an exception.
        """
        for stream_item in self._read():
            text = stream_item.decode().strip()
            if not text:
                continue

            # Kernel events always have this format:
            # event: <event>
            # data: <data>
            if "\n" not in text:
                raise ValueError(f"Unexpected event format: {text}")
            first_line, remaining = text.split("\n", 1)

            if not first_line.startswith("event: "):
                raise ValueError(f"Unexpected event prefix: {first_line}")
            event = first_line.split("event: ", 1)[1]

            if not remaining.startswith("data: "):
                raise ValueError(f"Unexpected data prefix: {remaining}")
            data = remaining.split("data: ", 1)[1]

            yield Event(event=event, data=json.loads(data))
