import os

from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
)

from pharia_skill.studio.client import StudioClient


class StudioOTLPSpanExporter(OTLPSpanExporter):
    """OTLP exporter configured for Studio backend.

    This exporter uses OpenTelemetry's OTLP HTTP/PROTOBUF exporter to send
    traces directly to Studio's traces_v2 endpoint.
    """

    def __init__(
        self,
        project_id: str,
    ):
        """Initialize the OTLP Studio exporter."""
        if (token := os.getenv("PHARIA_AI_TOKEN")) is None:
            raise ValueError(
                "No authentication token provided. Set PHARIA_AI_TOKEN environment variable."
            )

        if (endpoint := os.getenv("PHARIA_STUDIO_ADDRESS")) is None:
            raise ValueError(
                "No Studio endpoint provided. Set PHARIA_STUDIO_ADDRESS environment variable."
            )

        # Construct the full traces endpoint
        traces_endpoint = f"{endpoint}/api/projects/{project_id}/traces_v2"

        # Create the internal OTLP exporter
        super().__init__(
            endpoint=traces_endpoint,
            headers={"Authorization": f"Bearer {token}"},
        )

    @classmethod
    def with_project(
        cls,
        project_name: str,
    ) -> "StudioOTLPSpanExporter":
        """Create an exporter with a project name.

        Args:
            project_name: The name of the project
        """
        client = StudioClient.with_project(project_name)
        return cls(project_id=client.project_id)
