import os
from collections.abc import Sequence
from typing import Optional
from urllib.parse import urljoin

import requests
from dotenv import load_dotenv
from pydantic import BaseModel
from requests.exceptions import ConnectionError, MissingSchema

from pharia_skill.studio.exporter import SpanClient
from pharia_skill.studio.span import StudioSpan, StudioSpanList


class StudioProject(BaseModel):
    name: str
    description: Optional[str]


class StudioClient(SpanClient):
    """Client for communicating with Pharia Studio.

    The Studio instance is determined by the environment variable `PHARIA_STUDIO_ADDRESS`.

    Attributes:
      project_id (int, required): The unique identifier of the project currently in use.
    """

    def __init__(
        self,
        project_name: str,
    ) -> None:
        """Initializes the client.

        Runs a health check to check for a valid url of the Studio connection.
        It does not check for a valid authentication token, which happens later.

        Args:
            project_name (str, required): The human readable identifier provided by the user.
        """
        load_dotenv()
        self._token = os.environ["AA_API_TOKEN"]
        self._headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self._token}",
        }

        self.url = os.environ["PHARIA_STUDIO_ADDRESS"]

        self._check_connection()

        self._project_name = project_name
        self._project_id: int | None = None

    @classmethod
    def with_project(cls, project_name: str) -> "StudioClient":
        """Set up a client for a project.

        Will create the project if it does not exist.
        """
        studio_client = StudioClient(project_name=project_name)
        if (project_id := studio_client._get_project(project_name)) is None:
            project_id = studio_client.create_project(project_name)

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
                f"The given url of the studio client does not point to a healthy studio: {response.status_code}: {response.json()}"  # type: ignore
            ) from None

    @property
    def project_id(self) -> int:
        "the unique project_id for the project_name as assigned by Pharia Studio"
        if self._project_id is None:
            if (project_id := self._get_project(self._project_name)) is None:
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
            project (str, required): User provided name of the project.
            description (str, optional, default None): Description explaining the usage of the project.

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

    def submit_spans(self, spans: Sequence[StudioSpan]):
        """Sends the provided spans to Studio as a singular trace.

        The method fails if the span list is empty, has already been created or if
        spans belong to multiple traces.

        Args:
            spans (Sequence[StudioSpan], required): Spans to create the trace from. Created by exporting from a :class:`Tracer`.
        """
        if len(spans) == 0:
            raise ValueError("Tried to upload an empty trace")
        self._upload_trace(StudioSpanList(spans))

    def _upload_trace(self, trace: StudioSpanList):
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
