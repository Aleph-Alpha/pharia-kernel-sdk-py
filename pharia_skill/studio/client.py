import os
from typing import Optional, cast
from urllib.parse import urljoin

import requests
from dotenv import load_dotenv
from pydantic import BaseModel
from requests.exceptions import ConnectionError, MissingSchema


class StudioProject(BaseModel):
    name: str
    description: Optional[str]


class StudioClient:
    """Client for communicating with Pharia Studio.

    The Studio instance is determined by the environment variable `PHARIA_STUDIO_ADDRESS`.

    Attributes:
      project_id (int, required): The unique identifier of the project currently in use.
    """

    def __init__(self, project_name: str) -> None:
        """Initializes the client.

        Runs a health check to check for a valid url of the Studio connection.
        It does not check for a valid authentication token, which happens later.

        Args:
            project_name (str, required): The human readable identifier provided by the user.
        """
        load_dotenv()
        self._token = os.environ["PHARIA_AI_TOKEN"]
        self._headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self._token}",
        }

        self.url = os.environ["PHARIA_STUDIO_ADDRESS"]

        self._check_connection()

        self._project_name = project_name
        self._project_id: str | None = None

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
        url = urljoin(self.url, "/health")
        try:
            response = requests.get(
                url,
                headers=self._headers,
            )
        except MissingSchema:
            raise ValueError(
                "The given url of the studio client is invalid. Make sure to include http:// in your url."
            ) from None
        except ConnectionError:
            raise ValueError(
                "The given url of the studio client does not point to a server."
            ) from None
        try:
            response.raise_for_status()
        except requests.HTTPError:
            raise ValueError(
                f"The given url of the studio client does not point to a healthy studio: {response.status_code}: {response.text}"
            ) from None

    @property
    def project_id(self) -> str:
        "The unique project_id for the project_name as assigned by Pharia Studio"
        if self._project_id is None:
            if (project_id := self._get_project(self._project_name)) is None:
                raise ValueError(
                    f"Project {self._project_name} was not available. Consider creating it with `StudioClient.create_project`."
                )
            self._project_id = project_id
        return self._project_id

    def _get_project(self, project: str) -> str | None:
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
            return str(project_of_interest["project_id"])
        except StopIteration:
            return None

    def create_project(self, project: str, description: Optional[str] = None) -> str:
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
        return cast(str, response.json())

    def list_traces(self) -> list[str]:
        url = urljoin(self.url, f"/api/projects/{self.project_id}/traces_v2")
        response = requests.get(
            url,
            headers=self._headers,
        )
        response.raise_for_status()
        return cast(list[str], response.json()["traces"])

    def delete_project(self) -> None:
        url = urljoin(self.url, f"/api/projects/{self.project_id}")
        response = requests.delete(
            url,
            headers=self._headers,
        )
        response.raise_for_status()
