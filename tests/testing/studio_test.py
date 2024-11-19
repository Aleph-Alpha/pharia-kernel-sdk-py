from typing import Sequence

import pytest

from pharia_skill import Completion, CompletionRequest
from pharia_skill.testing import DevCsi
from pharia_skill.testing.studio import ExporterClient, StudioExporter, StudioSpan
from pharia_skill.testing.tracing import SpanStatus

from .conftest import from_json
from .tracing_test import Input, haiku


@pytest.mark.kernel
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


@pytest.mark.kernel
def test_studio_collector_uploads_spans():
    # Given a csi setup with the studio exporter
    csi = DevCsi()
    client = SpyClient()
    exporter = StudioExporter(client)
    csi.set_span_exporter(exporter)

    # When running the skill
    haiku(csi, Input(topic="oat milk"))

    # Then the spans are exported to the client
    assert len(client.spans) == 1
    assert len(client.spans[0]) == 3


class FailingCsi(DevCsi):
    def complete_all(self, requests: list[CompletionRequest]) -> list[Completion]:
        raise RuntimeError("Out of cheese")


class SpyClient(ExporterClient):
    def __init__(self):
        self.spans: list[Sequence[StudioSpan]] = []

    def submit_trace(self, data: Sequence[StudioSpan]) -> str:
        self.spans.append(data)
        return "submitted"


@pytest.mark.kernel
def test_csi_exception_is_traced():
    # Given a csi with a failing complete_all
    csi = FailingCsi()
    client = SpyClient()
    exporter = StudioExporter(client)
    csi.set_span_exporter(exporter)

    # When the skill is invoked
    with pytest.raises(RuntimeError, match="Out of cheese"):
        haiku(csi, Input(topic="oat milk"))

    # Then the spans are collected by the studio collector
    assert len(client.spans) == 1
    first, second = client.spans[0]
    assert first.name == "search"
    assert first.status == SpanStatus.OK
    assert second.name == "haiku"
    assert second.status == SpanStatus.ERROR


def test_traces_are_exported_together(inner_span: dict, outer_span: dict):
    # Given a csi with the studio exporter
    client = SpyClient()
    exporter = StudioExporter(client)

    # And given a parent and child span
    inner = from_json(inner_span)
    outer = from_json(outer_span)

    # When we export the inner span
    exporter.export([inner])

    # And then the outer span
    exporter.export([outer])

    # Then the spans are submitted to the client
    assert len(client.spans) == 1
    assert len(client.spans[0]) == 2


def test_no_traces_exported_without_root_span(inner_span: dict):
    # Given a csi with the studio exporter
    client = SpyClient()
    exporter = StudioExporter(client)

    # When we export a span without a root span
    exporter.export([from_json(inner_span)])
    exporter.export([from_json(inner_span)])

    # Then no traces are submitted
    assert len(client.spans) == 0


def test_inner_trace_is_matched_with_correct_parent(inner_span: dict, error_span: dict):
    # Given a csi with the studio exporter
    client = SpyClient()
    exporter = StudioExporter(client)

    inner = from_json(inner_span)
    outer = from_json(error_span)
    assert outer.context.trace_id != inner.context.trace_id  # type: ignore

    # When we export two spans with different trace ids
    exporter.export([inner])
    exporter.export([outer])

    # Then only the outer span is submitted
    assert len(client.spans) == 1
    assert len(client.spans[0]) == 1
