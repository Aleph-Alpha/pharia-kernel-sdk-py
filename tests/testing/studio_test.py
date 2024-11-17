import pytest

from pharia_skill import Completion, CompletionRequest
from pharia_skill.testing import DevCsi
from pharia_skill.testing.studio import StudioExporter
from pharia_skill.testing.tracing import SpanStatus

from .tracing_test import Input, haiku


def test_multiple_csi_instances_do_not_duplicate_exporters():
    """A user might use different `DevCsi` instances in the same process.

    Assert that the processors are not duplicated.
    """
    # Given two csi instances
    csi1 = DevCsi.with_studio(project="kernel-test")
    csi2 = DevCsi.with_studio(project="kernel-test")

    # Then only one exporter is attached
    assert len(csi1.provider()._active_span_processor._span_processors) == 1
    assert len(csi2.provider()._active_span_processor._span_processors) == 1


def test_multiple_csi_instances_with_different_projects():
    # Given two csi instances with different projects
    DevCsi.with_studio(project="kernel-test")

    # Then an error is raised when the second exporter is attached
    with pytest.raises(
        RuntimeError,
        match="There is already a studio exporter to a different project attached.",
    ):
        DevCsi.with_studio(project="kernel-test-2")


@pytest.mark.kernel
def test_studio_collector_uploads_spans():
    # Given a csi setup with the studio exporter
    csi = DevCsi.with_studio(project="kernel-test")

    # When running the skill
    haiku(csi, Input(topic="oat milk"))

    # Then the spans are collected by the studio collector
    assert isinstance(csi.exporter, StudioExporter)
    assert len(csi.exporter.spans) == 3
    assert csi.exporter.client.project_id == 786

    # And shutting down the exporter does not raise an error
    csi.exporter.shutdown()


class FailingCsi(DevCsi):
    def complete_all(self, requests: list[CompletionRequest]) -> list[Completion]:
        raise RuntimeError("Out of cheese")


@pytest.mark.kernel
def test_csi_exception_is_traced():
    # Given a csi with a failing complete_all
    csi = FailingCsi.with_studio(project="kernel-test")

    # When the skill is invoked
    with pytest.raises(RuntimeError, match="Out of cheese"):
        haiku(csi, Input(topic="oat milk"))

    # Then the spans are collected by the studio collector
    assert isinstance(csi.exporter, StudioExporter)
    first, second = csi.exporter.spans  # type: ignore
    assert first.name == "search"
    assert first.status == SpanStatus.OK
    assert second.name == "haiku"
    assert second.status == SpanStatus.ERROR

    # And shutting down the exporter does not raise an error
    csi.exporter.shutdown()
