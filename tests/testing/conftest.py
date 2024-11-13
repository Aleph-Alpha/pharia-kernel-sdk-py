import pytest


@pytest.fixture
def inner_span() -> dict:
    return {
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


@pytest.fixture
def outer_span() -> dict:
    return {
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
