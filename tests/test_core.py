"""
Tests for P8s core module.
"""

import pytest
from pydantic import ValidationError

from p8s.core.settings import AISettings, DatabaseSettings, Settings


class TestSettings:
    """Test Settings configuration."""

    def test_default_settings(self):
        """Test default settings are created correctly."""
        settings = Settings()

        assert settings.app_name == "P8s App"
        assert settings.debug is False
        assert settings.port == 8000
        assert settings.host == "0.0.0.0"

    def test_database_settings(self):
        """Test database settings defaults."""
        settings = DatabaseSettings()

        assert "sqlite" in settings.url
        assert settings.pool_size == 5
        assert settings.echo is False

    def test_ai_settings(self):
        """Test AI settings defaults."""
        settings = AISettings()

        assert settings.provider == "openai"
        assert settings.model == "gpt-4o-mini"
        assert settings.cache_enabled is True

    def test_cors_origins_parsing(self):
        """Test CORS origins can be parsed from JSON string."""
        import json
        import os

        # pydantic-settings requires JSON format for list fields
        os.environ["P8S_CORS_ORIGINS"] = json.dumps(
            ["http://localhost:3000", "http://localhost:5173"]
        )

        settings = Settings()

        # Clean up
        del os.environ["P8S_CORS_ORIGINS"]

        assert "http://localhost:3000" in settings.cors_origins
        assert "http://localhost:5173" in settings.cors_origins


class TestDatabaseSettings:
    """Test DatabaseSettings."""

    def test_pool_size_validation(self):
        """Test pool size must be within valid range."""
        settings = DatabaseSettings(pool_size=50)
        assert settings.pool_size == 50

    def test_invalid_pool_size(self):
        """Test invalid pool size raises error."""
        with pytest.raises(ValidationError):
            DatabaseSettings(pool_size=200)  # Max is 100
