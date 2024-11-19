from typing import Sequence

import pytest
from opentelemetry.sdk.trace import ReadableSpan

from pharia_skill import Completion, CompletionRequest
from pharia_skill.studio import SpanClient, StudioExporter, StudioSpan
from pharia_skill.studio.span import SpanStatus
from pharia_skill.testing import DevCsi

from .span_test import Input, haiku


class FailingCsi(DevCsi):
    """A csi that fails on the complete_all method."""

    def complete_all(self, requests: list[CompletionRequest]) -> list[Completion]:
        raise RuntimeError("Out of cheese")


class SpyClient(SpanClient):
    def __init__(self):
        self.spans: list[Sequence[StudioSpan]] = []

    def submit_spans(self, spans: Sequence[StudioSpan]):
        self.spans.append(spans)


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


def test_traces_are_exported_together(
    inner_span: ReadableSpan, outer_span: ReadableSpan
):
    # Given a csi with the studio exporter
    client = SpyClient()
    exporter = StudioExporter(client)

    # When we export the inner span
    exporter.export([inner_span])

    # And then the outer span
    exporter.export([outer_span])

    # Then the spans are submitted to the client
    assert len(client.spans) == 1
    assert len(client.spans[0]) == 2


def test_no_traces_exported_without_root_span(inner_span: ReadableSpan):
    # Given a csi with the studio exporter
    client = SpyClient()
    exporter = StudioExporter(client)

    # When we export a span without a root span
    exporter.export([inner_span])
    exporter.export([inner_span])

    # Then no traces are submitted
    assert len(client.spans) == 0


def test_inner_trace_is_matched_with_correct_parent(
    inner_span: ReadableSpan, error_span: ReadableSpan
):
    # Given a csi with the studio exporter
    client = SpyClient()
    exporter = StudioExporter(client)

    assert error_span.context.trace_id != inner_span.context.trace_id  # type: ignore

    # When we export two spans with different trace ids
    exporter.export([inner_span])
    exporter.export([error_span])

    # Then only the outer span is submitted
    assert len(client.spans) == 1
    assert len(client.spans[0]) == 1
