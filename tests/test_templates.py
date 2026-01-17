"""
Tests for P8s Template Engine (Jinja2 integration).
"""

from unittest.mock import MagicMock

import pytest


class TestTemplateConfigure:
    """Test template configuration."""

    def test_configure_import(self):
        """Test configure can be imported."""
        from p8s.templates import configure

        assert configure is not None


class TestRenderTemplate:
    """Test render_template function."""

    def test_render_template_import(self):
        """Test render_template can be imported."""
        from p8s.templates import render_template

        assert render_template is not None


class TestRenderString:
    """Test render_string function."""

    def test_render_string_import(self):
        """Test render_string can be imported."""
        from p8s.templates import render_string

        assert render_string is not None


class TestGetTemplate:
    """Test get_template function."""

    def test_get_template_import(self):
        """Test get_template can be imported."""
        from p8s.templates import get_template

        assert get_template is not None

    def test_get_template_requires_config(self):
        """Test get_template raises error if not configured."""
        import p8s.templates as templates_module
        from p8s.templates import get_template

        # Reset the module state
        templates_module._jinja_env = None

        with pytest.raises(RuntimeError, match="not configured"):
            get_template("test.html")


class TestContextProcessors:
    """Test context processor functionality."""

    def test_add_context_processor_import(self):
        """Test add_context_processor can be imported."""
        from p8s.templates import add_context_processor

        assert add_context_processor is not None

    def test_static_url_processor_import(self):
        """Test static_url_processor can be imported."""
        from p8s.templates import static_url_processor

        assert static_url_processor is not None

    def test_url_for_processor_import(self):
        """Test url_for_processor can be imported."""
        from p8s.templates import url_for_processor

        assert url_for_processor is not None

    def test_static_url_processor(self):
        """Test static_url_processor returns correct static function."""
        from p8s.templates import static_url_processor

        mock_request = MagicMock()
        result = static_url_processor(mock_request)

        assert "static" in result
        assert result["static"]("image.png") == "/static/image.png"


class TestGetEnvironment:
    """Test get_environment function."""

    def test_get_environment_import(self):
        """Test get_environment can be imported."""
        from p8s.templates import get_environment

        assert get_environment is not None

    def test_get_environment_requires_config(self):
        """Test get_environment raises error if not configured."""
        import p8s.templates as templates_module
        from p8s.templates import get_environment

        # Reset the module state
        templates_module._jinja_env = None

        with pytest.raises(RuntimeError, match="not configured"):
            get_environment()


class TestExports:
    """Test module exports."""

    def test_all_exports(self):
        """Test __all__ exports correct symbols."""
        from p8s.templates import __all__

        assert "configure" in __all__
        assert "render_template" in __all__
        assert "render_string" in __all__
        assert "get_template" in __all__
        assert "add_context_processor" in __all__
