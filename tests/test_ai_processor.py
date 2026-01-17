"""
Tests for P8s AI processor module.
"""

from unittest.mock import AsyncMock, patch

import pytest
from sqlmodel import Field

from p8s.ai.fields import AIField, VectorField
from p8s.ai.processor import (
    format_prompt,
    get_ai_field_metadata,
    get_vector_field_metadata,
    has_ai_fields,
    has_vector_fields,
)
from p8s.db.base import Model


class TestAIFieldMetadata:
    """Test AIField metadata extraction."""

    def test_get_ai_field_metadata(self):
        """Test extracting AIField metadata from model."""

        class TestModel(Model):
            name: str = Field(default="")
            description: str = Field(default="")
            summary: str = AIField(
                prompt="Summarize: {description}",
                source_fields=["description"],
            )

        metadata = get_ai_field_metadata(TestModel)

        assert "summary" in metadata
        assert metadata["summary"]["prompt"] == "Summarize: {description}"
        assert metadata["summary"]["source_fields"] == ["description"]

    def test_no_ai_fields(self):
        """Test model without AIFields."""

        class TestModel(Model):
            name: str = Field(default="")

        metadata = get_ai_field_metadata(TestModel)
        assert metadata == {}

    def test_has_ai_fields(self):
        """Test has_ai_fields helper."""

        class WithAI(Model):
            summary: str = AIField(prompt="test", source_fields=[])

        class WithoutAI(Model):
            name: str = Field(default="")

        assert has_ai_fields(WithAI)
        assert not has_ai_fields(WithoutAI)


class TestVectorFieldMetadata:
    """Test VectorField metadata extraction."""

    def test_get_vector_field_metadata(self):
        """Test extracting VectorField metadata from model."""

        class TestModel(Model):
            content: str = Field(default="")
            embedding: list[float] = VectorField(
                source_field="content",
                dimensions=1536,
            )

        metadata = get_vector_field_metadata(TestModel)

        assert "embedding" in metadata
        assert metadata["embedding"]["source_field"] == "content"
        assert metadata["embedding"]["dimensions"] == 1536

    def test_has_vector_fields(self):
        """Test has_vector_fields helper."""

        class WithVector(Model):
            embedding: list[float] = VectorField(source_field="text")

        class WithoutVector(Model):
            name: str = Field(default="")

        assert has_vector_fields(WithVector)
        assert not has_vector_fields(WithoutVector)


class TestFormatPrompt:
    """Test prompt formatting."""

    def test_format_prompt_simple(self):
        """Test simple prompt formatting."""

        class TestModel(Model):
            name: str = Field(default="")
            description: str = Field(default="")

        instance = TestModel(name="Test Product", description="A great product")

        result = format_prompt(
            "Generate SEO for {name}: {description}",
            instance,
            ["name", "description"],
        )

        assert result == "Generate SEO for Test Product: A great product"

    def test_format_prompt_missing_field(self):
        """Test prompt with missing field gracefully handles error."""

        class TestModel(Model):
            name: str = Field(default="")

        instance = TestModel(name="Test")

        # Should not raise, returns template as-is
        result = format_prompt(
            "Test {nonexistent}",
            instance,
            ["nonexistent"],
        )

        assert "nonexistent" in result

    def test_format_prompt_empty_values(self):
        """Test prompt with empty/None values."""

        class TestModel(Model):
            name: str | None = None

        instance = TestModel()

        result = format_prompt(
            "Name: {name}",
            instance,
            ["name"],
        )

        assert result == "Name: "


class TestAISettingsConfiguration:
    """Test AI settings configuration checks."""

    def test_ai_disabled_by_default(self):
        """Test AI is disabled by default."""
        from p8s.core.settings import AISettings

        settings = AISettings()

        assert not settings.enabled
        assert not settings.is_configured()

    def test_ai_needs_api_key(self):
        """Test AI needs API key to be configured."""
        from p8s.core.settings import AISettings

        # Enabled but no key
        settings = AISettings(enabled=True, provider="openai")
        assert not settings.is_configured()

        # Enabled with key
        settings = AISettings(enabled=True, provider="openai", openai_api_key="sk-test")
        assert settings.is_configured()

    def test_ollama_no_key_needed(self):
        """Test Ollama doesn't need API key."""
        from p8s.core.settings import AISettings

        settings = AISettings(enabled=True, provider="ollama")
        assert settings.is_configured()

    def test_get_api_key(self):
        """Test getting API key for provider."""
        from p8s.core.settings import AISettings

        settings = AISettings(
            openai_api_key="sk-openai",
            anthropic_api_key="sk-anthropic",
        )

        settings.provider = "openai"
        assert settings.get_api_key() == "sk-openai"

        settings.provider = "anthropic"
        assert settings.get_api_key() == "sk-anthropic"

        settings.provider = "ollama"
        assert settings.get_api_key() is None


class TestProcessAIFields:
    """Test AI field processing."""

    @pytest.mark.asyncio
    async def test_process_disabled(self):
        """Test processing is skipped when AI disabled."""
        from p8s.ai.processor import process_ai_fields

        class TestModel(Model):
            summary: str = AIField(prompt="test", source_fields=[])

        instance = TestModel()

        # Should return empty dict when disabled
        with patch("p8s.ai.processor.get_settings") as mock_settings:
            mock_settings.return_value.ai.enabled = False
            result = await process_ai_fields(instance)

        assert result == {}

    @pytest.mark.asyncio
    async def test_process_not_configured(self):
        """Test processing is skipped when not configured."""
        from p8s.ai.processor import process_ai_fields

        class TestModel(Model):
            summary: str = AIField(prompt="test", source_fields=[])

        instance = TestModel()

        with patch("p8s.ai.processor.get_settings") as mock_settings:
            mock_settings.return_value.ai.enabled = True
            mock_settings.return_value.ai.is_configured.return_value = False
            result = await process_ai_fields(instance)

        assert result == {}
