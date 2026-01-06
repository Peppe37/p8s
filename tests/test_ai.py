"""
Tests for P8s AI module.
"""

import pytest

from p8s.ai.fields import AIField, VectorField
from p8s.ai.config import AIConfig


class TestAIField:
    """Test AIField functionality."""

    def test_ai_field_creation(self):
        """Test AIField creates proper field info."""
        field = AIField(
            prompt="Generate SEO for: {description}",
            source_fields=["description"],
        )

        # Check it's a valid Pydantic field
        assert field is not None

    def test_ai_field_metadata(self):
        """Test AIField includes correct metadata."""
        from p8s.db.base import Model
        from sqlmodel import Field

        class Product(Model):
            name: str = Field(default="")
            description: str = Field(default="")
            seo: str = AIField(
                prompt="SEO for {name}",
                source_fields=["name"],
            )

        # Check field exists
        assert "seo" in Product.model_fields


class TestVectorField:
    """Test VectorField functionality."""

    def test_vector_field_creation(self):
        """Test VectorField creates proper field info."""
        field = VectorField(
            source_field="content",
            dimensions=1536,
        )

        assert field is not None

    def test_vector_field_custom_dimensions(self):
        """Test VectorField with custom dimensions."""
        field = VectorField(
            source_field="text",
            dimensions=768,
            model="text-embedding-ada-002",
        )

        assert field is not None


class TestAIConfig:
    """Test AIConfig class."""

    def test_default_config(self):
        """Test default AIConfig values."""
        config = AIConfig()

        assert config.provider == "openai"
        assert config.model == "gpt-4o-mini"
        assert config.temperature == 0.7
        assert config.cache_enabled is True

    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        data = {
            "provider": "anthropic",
            "model": "claude-3-opus",
            "temperature": 0.5,
        }

        config = AIConfig.from_dict(data)

        assert config.provider == "anthropic"
        assert config.model == "claude-3-opus"
        assert config.temperature == 0.5

    def test_config_to_dict(self):
        """Test converting config to dictionary."""
        config = AIConfig()
        data = config.to_dict()

        assert "provider" in data
        assert "model" in data
        assert "temperature" in data
        assert data["provider"] == "openai"
