import os

from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

from pharia_skill.studio.client import StudioClient


class StudioExporter(OTLPSpanExporter):
    """OTLP exporter configured for Studio backend.

    This exporter uses OpenTelemetry's OTLP HTTP/PROTOBUF exporter to send traces
    directly to Studio's traces_v2 endpoint.
    """

    def __init__(self, project_name: str):
        if (token := os.getenv("PHARIA_AI_TOKEN")) is None:
            raise ValueError(
                "No authentication token provided. Set PHARIA_AI_TOKEN environment variable."
            )

        if (endpoint := os.getenv("PHARIA_STUDIO_ADDRESS")) is None:
            raise ValueError(
                "No Studio endpoint provided. Set PHARIA_STUDIO_ADDRESS environment variable."
            )

        client = StudioClient.with_project(project_name)
        client.assert_new_trace_endpoint_is_available()
        traces_endpoint = f"{endpoint}/api/projects/{client.project_id}/traces_v2"
        headers = {"Authorization": f"Bearer {token}"}
        super().__init__(endpoint=traces_endpoint, headers=headers)
