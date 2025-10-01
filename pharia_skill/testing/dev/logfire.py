"""
While Pydantic Logfire claim to follow the OpenTelemetry Semantic Conventions for Generative AI systems,
they also state:

Moreover, those semantic conventions specify that messages should be captured as individual events
(logs) that are children of the request span, whereas by default, Pydantic AI instead collects
these events into a JSON array which is set as a single large attribute called events on the
request span.

This means that if we do want chat messages to be displayed in the UI, we need to add this events
explicitly. Further, a custom `logfire.json_schema` attribute is also needed to ensure that the
events are properly serialized.

See <https://ai.pydantic.dev/logfire/#alternative-observability-backends> for more details.

Langfuse is able to render the conversation history based on these Logfire events, see
<https://github.com/langfuse/langfuse/blob/main/packages/shared/src/server/otel/OtelIngestionProcessor.ts#L1030>
"""

import json
from typing import Any

from opentelemetry.trace import Span

from pharia_skill.csi.inference import Message


def set_logfire_attributes(
    span: Span, input_messages: list[Message], output_message: Message
) -> None:
    """Set attributes required for Pydantic Logfire to render chat conversations in the UI."""
    events = [as_logfire_input_event(m) for m in input_messages]
    events.append(as_logfire_output_event(output_message))

    span.set_attribute("events", json.dumps(events))
    span.set_attribute(
        "logfire.json_schema",
        json.dumps({"type": "object", "properties": {"events": {"type": "array"}}}),
    )


def as_logfire_input_event(message: Message) -> dict[str, Any]:
    return {
        "event.name": f"gen_ai.{message.role.value}.message",
        **message.as_gen_ai_otel_attributes(),
    }


def as_logfire_output_event(message: Message) -> dict[str, Any]:
    return {
        "event.name": "gen_ai.choice",
        **message.as_gen_ai_otel_attributes(),
    }
