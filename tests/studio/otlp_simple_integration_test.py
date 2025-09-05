"""
Simple integration tests for OTLP exporter that focus on configuration and setup.

These tests verify that the OTLP exporter can be properly configured and integrated
with the DevCsi system without requiring actual network calls.
"""

import os
from unittest.mock import patch

import pytest

from pharia_skill.studio.otlp_exporter import StudioOTLPSpanExporter
from pharia_skill.testing import DevCsi

from .conftest import StubCsiClient


def test_otlp_exporter_can_be_created_with_valid_config():
    """Test that OTLP exporter can be created with valid environment configuration."""
    with patch.dict(
        os.environ,
        {
            "PHARIA_AI_TOKEN": "test-token",
            "PHARIA_STUDIO_ADDRESS": "https://studio.example.com",
        },
    ):
        # Should not raise any exceptions
        exporter = StudioOTLPSpanExporter(project_id="test-project")
        assert exporter is not None


def test_otlp_exporter_can_be_set_on_devcsi():
    """Test that OTLP exporter can be set on DevCsi without errors."""
    with patch.dict(
        os.environ,
        {
            "PHARIA_AI_TOKEN": "test-token",
            "PHARIA_STUDIO_ADDRESS": "https://studio.example.com",
        },
    ):
        csi = DevCsi.__new__(DevCsi)
        csi.client = StubCsiClient()

        exporter = StudioOTLPSpanExporter(project_id="test-project")

        # Should not raise any exceptions
        csi.set_span_exporter(exporter)

        # Verify the exporter was set (check that it doesn't return None)
        existing_exporter = csi.existing_exporter()
        assert existing_exporter is not None


def test_otlp_exporter_replaces_studio_exporter_on_devcsi():
    """Test that setting OTLP exporter replaces any existing Studio exporter."""
    from pharia_skill.studio import StudioExporter

    from .conftest import SpyClient

    with patch.dict(
        os.environ,
        {
            "PHARIA_AI_TOKEN": "test-token",
            "PHARIA_STUDIO_ADDRESS": "https://studio.example.com",
        },
    ):
        csi = DevCsi.__new__(DevCsi)
        csi.client = StubCsiClient()

        # First set a regular Studio exporter
        studio_client = SpyClient()
        studio_exporter = StudioExporter(studio_client)
        csi.set_span_exporter(studio_exporter)

        # Verify it was set
        existing_exporter = csi.existing_exporter()
        assert existing_exporter is studio_exporter

        # Now set OTLP exporter
        otlp_exporter = StudioOTLPSpanExporter(project_id="test-project")
        csi.set_span_exporter(otlp_exporter)

        # Verify OTLP exporter replaced the Studio exporter
        existing_exporter = csi.existing_exporter()
        assert existing_exporter is otlp_exporter


def test_with_project_method_integration():
    """Test that with_project method works with mocked StudioClient."""
    with patch(
        "pharia_skill.studio.client.StudioClient.with_project"
    ) as mock_with_project:
        from unittest.mock import MagicMock

        mock_client = MagicMock()
        mock_client.project_id = "resolved-project-123"
        mock_with_project.return_value = mock_client

        with patch.dict(
            os.environ,
            {
                "PHARIA_AI_TOKEN": "test-token",
                "PHARIA_STUDIO_ADDRESS": "https://studio.example.com",
            },
        ):
            exporter = StudioOTLPSpanExporter.with_project("my-test-project")

            # Verify StudioClient.with_project was called
            mock_with_project.assert_called_once_with("my-test-project")

            # Verify exporter was created
            assert exporter is not None


def test_otlp_exporter_configuration_validation():
    """Test that OTLP exporter properly validates configuration."""
    # Test missing token
    with patch.dict(
        os.environ,
        {"PHARIA_STUDIO_ADDRESS": "https://studio.example.com"},
        clear=True,
    ):
        with pytest.raises(ValueError, match="No authentication token provided"):
            StudioOTLPSpanExporter(project_id="test-project")

    # Test missing studio address
    with patch.dict(os.environ, {"PHARIA_AI_TOKEN": "test-token"}, clear=True):
        with pytest.raises(ValueError, match="No Studio endpoint provided"):
            StudioOTLPSpanExporter(project_id="test-project")

    # Test both missing
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="No authentication token provided"):
            StudioOTLPSpanExporter(project_id="test-project")


def test_otlp_exporter_inherits_from_otlp_span_exporter():
    """Test that StudioOTLPSpanExporter inherits expected methods from OTLPSpanExporter."""
    with patch.dict(
        os.environ,
        {
            "PHARIA_AI_TOKEN": "test-token",
            "PHARIA_STUDIO_ADDRESS": "https://studio.example.com",
        },
    ):
        exporter = StudioOTLPSpanExporter(project_id="test-project")

        # Verify it has the expected methods from OTLPSpanExporter
        assert hasattr(exporter, "export")
        assert hasattr(exporter, "shutdown")
        assert hasattr(exporter, "force_flush")

        # Verify it's callable (these methods exist and can be called)
        assert callable(exporter.export)
        assert callable(exporter.shutdown)
        assert callable(exporter.force_flush)
