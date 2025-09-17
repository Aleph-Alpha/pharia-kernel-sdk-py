from opentelemetry.sdk.trace.export import SimpleSpanProcessor


class StudioSpanProcessor(SimpleSpanProcessor):
    """Signal that a processor has been registered by the SDK."""

    pass
