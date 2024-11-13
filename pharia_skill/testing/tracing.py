import datetime as dt
import json
from collections.abc import Sequence
from enum import Enum
from typing import Literal, Union
from uuid import UUID

from pydantic import BaseModel, Field, RootModel, SerializeAsAny, field_validator


def utc_now() -> dt.datetime:
    """Return datetime object with utc timezone.

    datetime.utcnow() returns a datetime object without timezone, so this function is preferred.
    """
    return dt.datetime.now(dt.timezone.utc)


def double_to_128bit(original_64bit_str: str) -> UUID:
    """Convert a 64-bit integer to a 128-bit UUID.

    OpenTelemetry uses 64-bit integers to represent trace IDs and span IDs.
    Studio expects 128-bit UUIDs. The mapping is injective, as the 64-bit integer
    binary representation is doubled to create the 128-bit number.
    """
    # Ensure the input is a 64-bit integer
    original_64bit = int(original_64bit_str, 16)

    # Double it to 128 bits by repeating it
    doubled_128bit = (original_64bit << 64) | original_64bit

    return UUID(int=doubled_128bit)


class Event(BaseModel):
    name: str
    message: str
    body: SerializeAsAny[BaseModel]
    timestamp: dt.datetime = Field(default_factory=utc_now)


class SpanType(str, Enum):
    SPAN = "SPAN"
    TASK_SPAN = "TASK_SPAN"


class SpanAttributes(BaseModel):
    type: Literal[SpanType.SPAN] = SpanType.SPAN


class TaskSpanAttributes(BaseModel):
    type: Literal[SpanType.TASK_SPAN] = SpanType.TASK_SPAN
    input: dict
    output: dict

    @field_validator("input", mode="before")
    def validate_input(cls, data: str):
        """Load a json string into an arbitrary pydantic model.

        OTel attributes do not support dictionary. The input and output is
        serialized to json and is stored as a string.
        """
        return json.loads(data)

    @field_validator("output", mode="before")
    def validate_output(cls, data: str):
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


class ExportedSpan(BaseModel):
    context: Context
    name: str | None
    parent_id: UUID | None
    start_time: dt.datetime
    end_time: dt.datetime
    attributes: Union[SpanAttributes, TaskSpanAttributes] = Field(discriminator="type")
    events: Sequence[Event]
    status: SpanStatus

    @field_validator("parent_id", mode="before")
    def validate_parent_id(cls, data: str | None) -> UUID | None:
        if data is None:
            return None
        return double_to_128bit(data)

    @field_validator("status", mode="before")
    def validate_status(cls, data: dict) -> SpanStatus:
        if data["status_code"] == "OK":
            return SpanStatus.OK
        return SpanStatus.ERROR


ExportedSpanList = RootModel[Sequence[ExportedSpan]]
