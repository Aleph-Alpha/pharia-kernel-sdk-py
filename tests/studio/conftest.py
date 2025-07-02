import datetime as dt
from typing import Any, Generator, Sequence

import pytest
from opentelemetry.sdk.trace import Event as OtelEvent
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.trace.span import SpanContext
from opentelemetry.trace.status import Status, StatusCode

from pharia_skill.studio import SpanClient, StudioSpan
from pharia_skill.testing import DevCsi
from pharia_skill.testing.dev.client import CsiClient, Event


class SpyClient(SpanClient):
    def __init__(self) -> None:
        self.spans: list[Sequence[StudioSpan]] = []

    def submit_spans(self, spans: Sequence[StudioSpan]):
        self.spans.append(spans)


class StubCsiClient(CsiClient):
    """Use the `DevCsi` without doing any http calls to the Kernel."""

    def __init__(self) -> None:
        self.events: list[Event] = []

    def run(self, function: str, data: Any) -> Any:
        completion = {
            "text": "Hello, world!",
            "finish_reason": "stop",
            "logprobs": [],
            "usage": {"prompt": 1, "completion": 1},
        }
        match function:
            case "complete":
                return [completion]
            case "search":
                return [[]]
            case _:
                return {}

    def stream(
        self, function: str, data: dict[str, Any]
    ) -> Generator[Event, None, None]:
        yield from self.events


@pytest.fixture
def stub_dev_csi() -> DevCsi:
    """Create a `DevCsi` without requiring any env variables or setting up a session."""
    csi = DevCsi.__new__(DevCsi)
    csi.client = StubCsiClient()
    return csi


@pytest.fixture
def inner_span() -> ReadableSpan:
    """A children span to `outer_span`."""
    return span_from_json(
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
    return span_from_json(
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
    return span_from_json(
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


def span_from_json(inner_span: dict[str, Any]) -> ReadableSpan:
    """Load an OpenTelemetry span from it's JSON representation.

    When tracing, spans can easily be exported to json with `span.to_json()`.
    This function allows to load them for testing purposes.
    """
    context = SpanContext(
        trace_id=int(inner_span["context"]["trace_id"], 16),
        span_id=int(inner_span["context"]["span_id"], 16),
        is_remote=False,
    )
    parent = (
        SpanContext(
            trace_id=int(inner_span["context"]["trace_id"], 16),
            span_id=int(inner_span["parent_id"], 16),
            is_remote=False,
        )
        if inner_span["parent_id"]
        else None
    )
    status = Status(
        status_code=status_str_to_status(inner_span["status"]["status_code"]),
        description=inner_span["status"].get("description"),
    )
    events = [
        OtelEvent(
            name=event["name"],
            timestamp=timestamp_from_iso(event["timestamp"]),
            attributes=event["attributes"],
        )
        for event in inner_span["events"]
    ]
    return ReadableSpan(
        name=inner_span["name"],
        attributes=inner_span["attributes"],
        links=inner_span["links"],
        parent=parent,
        context=context,
        status=status,
        events=events,
        start_time=timestamp_from_iso(inner_span["start_time"]),
        end_time=timestamp_from_iso(inner_span["end_time"]),
    )


def status_str_to_status(status_str: str) -> StatusCode:
    match status_str:
        case "OK":
            return StatusCode.OK
        case "ERROR":
            return StatusCode.ERROR
        case _:
            raise ValueError(f"Unknown status code: {status_str}")


def timestamp_from_iso(iso_str: str) -> int:
    return int(dt.datetime.fromisoformat(iso_str).timestamp())
