import os
from unittest.mock import MagicMock, patch

import pytest

from pharia_skill.studio.otlp_exporter import StudioOTLPSpanExporter


def test_initialization_with_valid_env_vars():
    """Test successful initialization with valid environment variables."""
    with patch.dict(
        os.environ,
        {
            "PHARIA_AI_TOKEN": "test-token",
            "PHARIA_STUDIO_ADDRESS": "https://studio.example.com",
        },
    ):
        exporter = StudioOTLPSpanExporter(project_id="test-project-123")

        # Verify the endpoint is constructed correctly
        assert (
            exporter._endpoint
            == "https://studio.example.com/api/projects/test-project-123/traces_v2"
        )
        # Verify the headers contain the authorization token
        assert exporter._headers["Authorization"] == "Bearer test-token"


def test_initialization_missing_token_raises_error():
    """Test that missing PHARIA_AI_TOKEN raises ValueError."""
    with patch.dict(
        os.environ,
        {"PHARIA_STUDIO_ADDRESS": "https://studio.example.com"},
        clear=True,
    ):
        with pytest.raises(ValueError, match="No authentication token provided"):
            StudioOTLPSpanExporter(project_id="test-project-123")


def test_initialization_missing_endpoint_raises_error():
    """Test that missing PHARIA_STUDIO_ADDRESS raises ValueError."""
    with patch.dict(os.environ, {"PHARIA_AI_TOKEN": "test-token"}, clear=True):
        with pytest.raises(ValueError, match="No Studio endpoint provided"):
            StudioOTLPSpanExporter(project_id="test-project-123")


def test_initialization_missing_both_env_vars_raises_error():
    """Test that missing both environment variables raises ValueError."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="No authentication token provided"):
            StudioOTLPSpanExporter(project_id="test-project-123")


def test_endpoint_construction_with_trailing_slash():
    """Test endpoint construction when studio address has trailing slash."""
    with patch.dict(
        os.environ,
        {
            "PHARIA_AI_TOKEN": "test-token",
            "PHARIA_STUDIO_ADDRESS": "https://studio.example.com/",
        },
    ):
        exporter = StudioOTLPSpanExporter(project_id="test-project-123")
        assert (
            exporter._endpoint
            == "https://studio.example.com//api/projects/test-project-123/traces_v2"
        )


def test_endpoint_construction_without_trailing_slash():
    """Test endpoint construction when studio address has no trailing slash."""
    with patch.dict(
        os.environ,
        {
            "PHARIA_AI_TOKEN": "test-token",
            "PHARIA_STUDIO_ADDRESS": "https://studio.example.com",
        },
    ):
        exporter = StudioOTLPSpanExporter(project_id="test-project-123")
        assert (
            exporter._endpoint
            == "https://studio.example.com/api/projects/test-project-123/traces_v2"
        )


@patch("pharia_skill.studio.client.StudioClient.with_project")
def test_with_project_class_method(mock_with_project):
    """Test the with_project class method creates exporter correctly."""
    # Mock the StudioClient to return a client with a specific project_id
    mock_client = MagicMock()
    mock_client.project_id = "project-456"
    mock_with_project.return_value = mock_client

    with patch.dict(
        os.environ,
        {
            "PHARIA_AI_TOKEN": "test-token",
            "PHARIA_STUDIO_ADDRESS": "https://studio.example.com",
        },
    ):
        exporter = StudioOTLPSpanExporter.with_project("test-project-name")

        # Verify StudioClient.with_project was called with the correct project name
        mock_with_project.assert_called_once_with("test-project-name")

        # Verify the exporter was initialized with the correct project_id
        assert (
            exporter._endpoint
            == "https://studio.example.com/api/projects/project-456/traces_v2"
        )


def test_inheritance_from_otlp_span_exporter():
    """Test that StudioOTLPSpanExporter properly inherits from OTLPSpanExporter."""
    with patch.dict(
        os.environ,
        {
            "PHARIA_AI_TOKEN": "test-token",
            "PHARIA_STUDIO_ADDRESS": "https://studio.example.com",
        },
    ):
        exporter = StudioOTLPSpanExporter(project_id="test-project-123")

        # Verify it has the expected methods from the parent class
        assert hasattr(exporter, "export")
        assert hasattr(exporter, "shutdown")
        assert hasattr(exporter, "force_flush")


def test_headers_format():
    """Test that authorization headers are formatted correctly."""
    with patch.dict(
        os.environ,
        {
            "PHARIA_AI_TOKEN": "my-secret-token-123",
            "PHARIA_STUDIO_ADDRESS": "https://studio.example.com",
        },
    ):
        exporter = StudioOTLPSpanExporter(project_id="test-project-123")
        assert "Authorization" in exporter._headers
        assert exporter._headers["Authorization"] == "Bearer my-secret-token-123"


def test_project_id_in_endpoint():
    """Test that project_id is correctly embedded in the endpoint URL."""
    with patch.dict(
        os.environ,
        {
            "PHARIA_AI_TOKEN": "test-token",
            "PHARIA_STUDIO_ADDRESS": "https://studio.example.com",
        },
    ):
        project_id = "special-project-789"
        exporter = StudioOTLPSpanExporter(project_id=project_id)
        expected_endpoint = (
            f"https://studio.example.com/api/projects/{project_id}/traces_v2"
        )
        assert exporter._endpoint == expected_endpoint
