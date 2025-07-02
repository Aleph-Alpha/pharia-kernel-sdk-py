import pytest
from pydantic import BaseModel

from pharia_skill import CompletionParams, CompletionRequest, Csi, IndexPath, skill
from pharia_skill.studio import StudioClient, StudioExporter
from pharia_skill.testing import DevCsi

from .conftest import SpyClient


# Given a skill
class Input(BaseModel):
    topic: str


class Output(BaseModel):
    haiku: str


@skill
def haiku(csi: Csi, input: Input) -> Output:
    """Skill with two csi calls for tracing."""
    index = IndexPath("f13", "wikipedia-de", "luminous-base-asymmetric-64")
    csi.search(index, input.topic, 1, 0.5)

    request = CompletionRequest(
        model="llama-3.1-8b-instruct",
        prompt=input.topic,
        params=CompletionParams(max_tokens=64),
    )
    result = csi.complete_concurrent([request, request])
    return Output(haiku=result[0].text)


@pytest.mark.kernel
@pytest.mark.studio
def test_trace_upload_studio_does_not_raise(stub_dev_csi: DevCsi):
    """Errors from uploading traces are handled by ErrorHandles.
    The default handling is silently ignoring the exceptions.

    Therefore, we explicitly collect the spans and upload them manually.
    """
    # Given a csi setup with the studio exporter
    client = SpyClient()
    exporter = StudioExporter(client)
    stub_dev_csi.set_span_exporter(exporter)

    # When running a skill and collecting spans
    haiku(stub_dev_csi, Input(topic="oat milk"))

    # Then no error is raised when running the skill
    StudioClient("kernel-test").submit_spans(client.spans[0])
