from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.trace import SpanContext, Status, StatusCode

from pharia_skill.studio.span import SpanStatus, StudioSpan, double_to_128bit


def test_convert_to_uuid():
    result = double_to_128bit("0xd1bf874f6554fe2b")
    assert str(result) == "d1bf874f-6554-fe2b-d1bf-874f6554fe2b"


def test_exported_span_from_csi_call(inner_span: ReadableSpan):
    # When validating a span created from tracing a csi call
    exported_span = StudioSpan.from_otel(inner_span)

    # Then the span is validated successfully
    assert exported_span.name == "complete"

    # And can be dumped to json
    exported_span.model_dump_json()


def test_exported_span_from_skill(outer_span: ReadableSpan):
    # When validating a span created from tracing a skill
    exported_span = StudioSpan.from_otel(outer_span)

    # Then the span is validated successfully
    assert exported_span.name == "haiku"

    # And can be dumped to json
    exported_span.model_dump_json()


def test_exported_span_from_error(error_span: ReadableSpan):
    # When validating a span created from tracing an error
    exported_span = StudioSpan.from_otel(error_span)

    # Then the status is set to error
    assert exported_span.status == SpanStatus.ERROR
    assert exported_span.events[0].message == "out of cheese"
    assert exported_span.events[0].name == "ValueError"
    # And can be dumped to json
    exported_span.model_dump_json()


def test_exported_span_without_status_is_ok():
    # Given an otel ReadableSpan without a status
    span = ReadableSpan(
        name="test",
        status=Status(StatusCode.UNSET),
        context=SpanContext(trace_id=1, span_id=2, is_remote=False),
        start_time=1,
        end_time=2,
        attributes={
            "input": '{"topic": "oat milk"}',
            "output": '{"haiku": "oat milk"}',
        },
        events=[],
    )
    assert span.status.status_code == StatusCode.UNSET

    # When converting to a studio span
    exported_span = StudioSpan.from_otel(span)

    # Then the status is set to ok
    assert exported_span.status == SpanStatus.OK
