import pytest

from pharia_skill.testing import DevCsi
from pharia_skill.testing.studio import StudioExporter

from .tracing_test import Input, haiku


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
