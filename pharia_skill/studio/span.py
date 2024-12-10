"""
Convert OpenTelemetry spans to the studio format.

The `StudioSpan` model provides the translation from an OpenTelemetry span
to the studio format. It can be set up from an OpenTelemetry span object and
can be (in serialized form) uploaded to the studio collector.

The `StudioSpan` model was copied over from the `ExportedSpan` model in the
intelligence layer. Each occurrence of a field validator marks one translation
step.
"""

import datetime as dt
import json
from collections.abc import Sequence
from enum import Enum
from typing import Any, Self
from uuid import UUID

from opentelemetry.sdk.trace import ReadableSpan
from pydantic import BaseModel, Field, RootModel, field_validator, model_validator


def utc_now() -> dt.datetime:
    """Return datetime object with utc timezone.

    datetime.utcnow() returns a datetime object without timezone, so this function is preferred.
    """
    return dt.datetime.now(dt.timezone.utc)


def double_to_128bit(double_str: str) -> UUID:
    """Convert a 64-bit integer to a 128-bit UUID.

    OpenTelemetry uses 64-bit integers to represent trace IDs and span IDs.
    Studio expects 128-bit UUIDs. The mapping is injective, as the 64-bit integer
    binary representation is doubled to create the 128-bit number.
    """
    double = int(double_str, 16)
    return UUID(int=((double << 64) | double))


class Event(BaseModel):
    name: str
    timestamp: dt.datetime = Field(default_factory=utc_now)

    # Use the attributes field for this as there is no concept of body in OTel events
    body: dict[str, Any] = Field(default_factory=dict, alias="attributes")
    message: str = ""

    @model_validator(mode="after")
    def message_and_name_for_errors(self) -> Self:
        """
        OpenTelemetry does not have the concept of a message for events.

        For errors, set the error message as message and the type as name.
        """
        self.message = self.body.get("exception.message", self.message)
        self.name = self.body.get("exception.type", self.name)
        return self


class TaskSpanAttributes(BaseModel):
    # Needed by the studio to identify task spans
    type: str = "TASK_SPAN"
    input: Any

    # Output is optional as it is not available on exceptions
    output: Any | None = None

    @field_validator("input", mode="before")
    def validate_input(cls, data: str) -> Any:
        """Load a json string into an arbitrary pydantic model.

        OTel attributes do not support dictionary. The input and output is
        serialized to json and is stored as a string.
        """
        return json.loads(data)

    @field_validator("output", mode="before")
    def validate_output(cls, data: str) -> Any:
        return json.loads(data)


class SpanStatus(Enum):
    OK = "OK"
    ERROR = "ERROR"


class Context(BaseModel):
    trace_id: UUID
    span_id: UUID

    @field_validator("trace_id", mode="before")
    def validate_trace_id(cls, data: str) -> UUID:
        """OpenTelemetry uses 128bit hex string to represent trace_id."""
        return UUID(int=int(data, 16))

    @field_validator("span_id", mode="before")
    def validate_span_id(cls, data: str) -> UUID:
        return double_to_128bit(data)


class StudioSpan(BaseModel):
    """Specifies the span/trace data model than can be exported to studio.

    Can be created from an OpenTelemetry span.
    """

    context: Context
    name: str | None
    parent_id: UUID | None
    start_time: dt.datetime
    end_time: dt.datetime
    attributes: TaskSpanAttributes
    events: Sequence[Event]
    status: SpanStatus

    @field_validator("parent_id", mode="before")
    def validate_parent_id(cls, data: str | None) -> UUID | None:
        if data is None:
            return None
        return double_to_128bit(data)

    @field_validator("status", mode="before")
    def validate_status(cls, data: dict[str, str]) -> SpanStatus:
        if data["status_code"] == "OK":
            return SpanStatus.OK
        return SpanStatus.ERROR

    @classmethod
    def from_otel(cls, span: ReadableSpan) -> "StudioSpan":
        """Convert an OpenTelemetry span to the studio format."""
        return cls.model_validate(json.loads(span.to_json()))


StudioSpanList = RootModel[Sequence[StudioSpan]]
