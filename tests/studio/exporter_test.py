import random
import string
from collections.abc import Iterator

import pytest
from pydantic import BaseModel

from pharia_skill import Csi, Message, skill
from pharia_skill.studio import StudioClient
from pharia_skill.testing import DevCsi


@pytest.fixture
def temp_project_client() -> Iterator[StudioClient]:
    """A Studio client configured with a temporary project."""
    random_string = "".join(random.choices(string.ascii_letters + string.digits, k=10))
    name = "Tracing Test: " + random_string
    client = StudioClient.with_project(name)
    try:
        yield client
    finally:
        client.delete_project()


@pytest.mark.studio
def test_otlp_trace_export_to_studio(temp_project_client: StudioClient):
    # Given a skill that does a chat request
    class Input(BaseModel):
        messages: list[Message]

    class Output(BaseModel):
        text: str

    @skill
    def haiku(csi: Csi, input: Input) -> Output:
        result = csi.chat(model="llama-3.1-8b-instruct", messages=input.messages)
        return Output(text=result.message.content)

    # And given a csi configured with the studio exporter
    csi = DevCsi(project=temp_project_client._project_name)

    # When running the skill against the csi
    haiku(csi, Input(messages=[Message.user("Hi")]))

    # Then the spans are exported to studio
    assert len(temp_project_client.list_traces()) == 1
