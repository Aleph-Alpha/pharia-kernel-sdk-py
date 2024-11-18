import os
from collections import defaultdict
from collections.abc import Sequence
from typing import Optional
from urllib.parse import urljoin

import requests
from dotenv import load_dotenv
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
from pydantic import BaseModel
from requests.exceptions import ConnectionError, MissingSchema

from pharia_skill.testing.tracing import (
    StudioSpan,
    StudioSpanList,
)


class StudioProject(BaseModel):
    name: str
    description: Optional[str]


class StudioClient:
    """Client for communicating with Studio.

    Attributes:
      project_id: The unique identifier of the project currently in use.
      url: The url of your current Studio instance.
    """

    def __init__(
        self,
        project: str,
    ) -> None:
        """Initializes the client.

        Runs a health check to check for a valid url of the Studio connection.
        It does not check for a valid authentication token, which happens later.

        Args:
            project: The human readable identifier provided by the user.
        """
        load_dotenv()
        self._token = os.environ["AA_API_TOKEN"]
        self._headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self._token}",
        }

        self.url = os.environ["PHARIA_STUDIO_ADDRESS"]

        self._check_connection()

        self._project_name = project
        self._project_id: int | None = None

    @classmethod
    def with_project(cls, project: str) -> "StudioClient":
        """Set up a client for a project.

        Will create the project if it does not exist.
        """
        studio_client = StudioClient(project=project)
        if (project_id := studio_client._get_project(project)) is None:
            project_id = studio_client.create_project(project)

        assert project_id is not None
        studio_client._project_id = project_id
        return studio_client

    def _check_connection(self) -> None:
        try:
            url = urljoin(self.url, "/health")
            response = requests.get(
                url,
                headers=self._headers,
            )
            response.raise_for_status()
        except MissingSchema:
            raise ValueError(
                "The given url of the studio client is invalid. Make sure to include http:// in your url."
            ) from None
        except ConnectionError:
            raise ValueError(
                "The given url of the studio client does not point to a server."
            ) from None
        except requests.HTTPError:
            raise ValueError(
                f"The given url of the studio client does not point to a healthy studio: {response.status_code}: {response.json()}"
            ) from None

    @property
    def project_id(self) -> int:
        if self._project_id is None:
            project_id = self._get_project(self._project_name)
            if project_id is None:
                raise ValueError(
                    f"Project {self._project_name} was not available. Consider creating it with `StudioClient.create_project`."
                )
            self._project_id = project_id
        return self._project_id

    def _get_project(self, project: str) -> int | None:
        url = urljoin(self.url, "/api/projects")
        response = requests.get(
            url,
            headers=self._headers,
        )
        response.raise_for_status()
        all_projects = response.json()
        try:
            project_of_interest = next(
                proj for proj in all_projects if proj["name"] == project
            )
            return int(project_of_interest["id"])
        except StopIteration:
            return None

    def create_project(self, project: str, description: Optional[str] = None) -> int:
        """Creates a project in Studio.

        Projects are uniquely identified by the user provided name.

        Args:
            project: User provided name of the project.
            description: Description explaining the usage of the project. Defaults to None.

        Returns:
            The ID of the newly created project.
        """
        url = urljoin(self.url, "/api/projects")
        data = StudioProject(name=project, description=description)
        response = requests.post(
            url,
            data=data.model_dump_json(),
            headers=self._headers,
        )
        match response.status_code:
            case 409:
                raise ValueError("Project already exists")
            case _:
                response.raise_for_status()
        return int(response.text)

    def submit_trace(self, data: Sequence[StudioSpan]) -> str:
        """Sends the provided spans to Studio as a singular trace.

        The method fails if the span list is empty, has already been created or if
        spans belong to multiple traces.

        Args:
            data: :class:`Spans` to create the trace from. Created by exporting from a :class:`Tracer`.

        Returns:
            The ID of the created trace.
        """
        if len(data) == 0:
            raise ValueError("Tried to upload an empty trace")
        return self._upload_trace(StudioSpanList(data))

    def _upload_trace(self, trace: StudioSpanList) -> str:
        url = urljoin(self.url, f"/api/projects/{self.project_id}/traces")
        response = requests.post(
            url,
            data=trace.model_dump_json(),
            headers=self._headers,
        )
        match response.status_code:
            case 409:
                raise ValueError(
                    f"Trace with id {trace.root[0].context.trace_id} already exists."
                )
            case 422:
                raise ValueError(
                    f"Uploading the trace failed with 422. Response: {response.json()}"
                )
            case _:
                response.raise_for_status()
        return str(response.json())


class StudioExporter(SpanExporter):
    """An OpenTelemetry exporter that uploads spans to Studio.

    The exporter will create a project on setup if it does not exist yet.
    """

    def __init__(self, project: str):
        self.spans: list[StudioSpan] = []
        self.client = StudioClient.with_project(project)

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        """Store spans in the exporter and upload them to Studio when the exporter shuts down.

        Studio is complaining about duplicate IDs when uploading traces with the same `span_id`
        in separate requests. Therefore, we store the spans in a list and only upload them
        when the exporter shuts down.
        """
        studio_spans = [StudioSpan.from_otel(span) for span in spans]
        self.spans.extend(studio_spans)
        return SpanExportResult.SUCCESS

    def shutdown(self):
        """Upload the collected spans to Studio.

        Upload spans belonging to the same trace together
        """
        # split spans by trace_id
        traces = defaultdict(list)
        for span in self.spans:
            traces[span.context.trace_id].append(span)

        for trace in traces.values():
            self.client.submit_trace(trace)
        self.spans.clear()
