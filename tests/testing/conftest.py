import datetime as dt

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import Event, ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
    SpanExporter,
    SpanExportResult,
)
from opentelemetry.trace.span import SpanContext
from opentelemetry.trace.status import Status, StatusCode


class InMemorySpanExporter(SpanExporter):
    """An OpenTelemetry span exporter that stores spans in memory.

    Can be used for testing purposes.
    """

    def __init__(self):
        self.finished_spans = []

    def export(self, spans):
        self.finished_spans.extend(spans)
        return SpanExportResult.SUCCESS

    def shutdown(self):
        self.finished_spans.clear()


@pytest.fixture(scope="module")
def provider() -> TracerProvider:
    if not isinstance(trace.get_tracer_provider(), TracerProvider):
        trace_provider = TracerProvider()
        trace.set_tracer_provider(trace_provider)

    return trace.get_tracer_provider()  # type: ignore


@pytest.fixture
def exporter(provider: TracerProvider) -> InMemorySpanExporter:
    exporter = InMemorySpanExporter()
    span_processor = SimpleSpanProcessor(exporter)
    provider.add_span_processor(span_processor)
    return exporter


@pytest.fixture
def inner_span() -> ReadableSpan:
    """A children span to `outer_span`."""
    return from_json(
        {
            "name": "complete",
            "context": {
                "trace_id": "0xbf1bd6a9821572d268a6b1624b2db5ed",
                "span_id": "0x61aa9d8872df195e",
                "trace_state": "[]",
            },
            "kind": "SpanKind.INTERNAL",
            "parent_id": "0x0518819f195c3f15",
            "start_time": "2024-11-14T13:17:13.381386Z",
            "end_time": "2024-11-14T13:17:14.485530Z",
            "status": {"status_code": "OK"},
            "attributes": {
                "type": "TASK_SPAN",
                "input": '{"prompt": "oat milk", "model": "llama-3.1-8b-instruct", "params": {"max_tokens": 64, "temperature": null, "top_k": null, "top_p": null, "stop": []}, "version": "0.2", "function": "complete"}',
                "output": '{"finish_reason": "length", "text": ", and other plant-based milks. The company also offers a range of dairy-free yogurt alternatives made from coconut milk, almond milk, and other plant-based milks.\\nIn addition to its dairy-free products, So Delicious also offers a range of other products, including:\\n* Frozen desserts: So Delicious offers a range of"}',
            },
            "events": [],
            "links": [],
            "resource": {
                "attributes": {
                    "telemetry.sdk.language": "python",
                    "telemetry.sdk.name": "opentelemetry",
                    "telemetry.sdk.version": "1.28.1",
                    "service.name": "unknown_service",
                },
                "schema_url": "",
            },
        }
    )


@pytest.fixture
def outer_span() -> ReadableSpan:
    """A parent span to `inner_span`."""
    return from_json(
        {
            "name": "haiku",
            "context": {
                "trace_id": "0xbf1bd6a9821572d268a6b1624b2db5ed",
                "span_id": "0x0518819f195c3f15",
                "trace_state": "[]",
            },
            "kind": "SpanKind.INTERNAL",
            "parent_id": None,
            "start_time": "2024-11-14T13:17:13.381318Z",
            "end_time": "2024-11-14T13:17:14.485625Z",
            "status": {"status_code": "OK"},
            "attributes": {
                "type": "TASK_SPAN",
                "input": '{"input": "oat milk"}',
                "output": '{"output": ", and other plant-based milks. The company also offers a range of dairy-free yogurt alternatives made from coconut milk, almond milk, and other plant-based milks.\\nIn addition to its dairy-free products, So Delicious also offers a range of other products, including:\\n* Frozen desserts: So Delicious offers a range of"}',
            },
            "events": [],
            "links": [],
            "resource": {
                "attributes": {
                    "telemetry.sdk.language": "python",
                    "telemetry.sdk.name": "opentelemetry",
                    "telemetry.sdk.version": "1.28.1",
                    "service.name": "unknown_service",
                },
                "schema_url": "",
            },
        }
    )


@pytest.fixture
def error_span() -> ReadableSpan:
    """A root level span with an error status. Not related to any other span."""
    return from_json(
        {
            "name": "haiku",
            "context": {
                "trace_id": "0x42b14b8889b0b6b79d0decfb21e2254f",
                "span_id": "0x844bce85fb833055",
                "trace_state": "[]",
            },
            "kind": "SpanKind.INTERNAL",
            "parent_id": None,
            "start_time": "2024-11-17T21:18:33.283500Z",
            "end_time": "2024-11-17T21:18:33.285685Z",
            "status": {
                "status_code": "ERROR",
                "description": "ValueError: out of cheese",
            },
            "attributes": {"type": "TASK_SPAN", "input": "{}"},
            "events": [
                {
                    "name": "exception",
                    "timestamp": "2024-11-17T21:18:33.285586Z",
                    "attributes": {
                        "exception.type": "ValueError",
                        "exception.message": "out of cheese",
                        "exception.stacktrace": "Traceback (most recent call last):",
                        "exception.escaped": "False",
                    },
                }
            ],
            "links": [],
            "resource": {
                "attributes": {
                    "telemetry.sdk.language": "python",
                    "telemetry.sdk.name": "opentelemetry",
                    "telemetry.sdk.version": "1.28.1",
                    "service.name": "unknown_service",
                },
                "schema_url": "",
            },
        }
    )


def status_str_to_status(status_str: str) -> StatusCode:
    match status_str:
        case "OK":
            return StatusCode.OK
        case "ERROR":
            return StatusCode.ERROR
        case _:
            raise ValueError(f"Unknown status code: {status_str}")


def from_json(inner_span: dict) -> ReadableSpan:
    return ReadableSpan(
        name=inner_span["name"],
        parent=SpanContext(
            trace_id=int(inner_span["context"]["trace_id"], 16),
            span_id=int(inner_span["parent_id"], 16),
            is_remote=False,
        )
        if inner_span["parent_id"]
        else None,
        context=SpanContext(
            trace_id=int(inner_span["context"]["trace_id"], 16),
            span_id=int(inner_span["context"]["span_id"], 16),
            is_remote=False,
        ),
        start_time=int(dt.datetime.fromisoformat(inner_span["start_time"]).timestamp()),
        end_time=int(dt.datetime.fromisoformat(inner_span["end_time"]).timestamp()),
        attributes=inner_span["attributes"],
        status=Status(
            status_code=status_str_to_status(inner_span["status"]["status_code"]),
            description=inner_span["status"].get("description"),
        ),
        events=[
            Event(
                name=event["name"],
                timestamp=int(
                    dt.datetime.fromisoformat(event["timestamp"]).timestamp()
                ),
                attributes=event["attributes"],
            )
            for event in inner_span["events"]
        ],
        links=inner_span["links"],
    )
