"""
Tests for P8s admin inlines functionality.
"""

from dataclasses import dataclass

import pytest


class TestInlineConfig:
    """Test inline configuration classes."""

    def test_tabular_inline_import(self):
        """Test TabularInline can be imported."""
        from p8s.admin.inlines import TabularInline

        assert TabularInline is not None

    def test_stacked_inline_import(self):
        """Test StackedInline can be imported."""
        from p8s.admin.inlines import StackedInline

        assert StackedInline is not None

    def test_inline_config_defaults(self):
        """Test InlineConfig default values."""
        from p8s.admin.inlines import InlineConfig

        config = InlineConfig()

        assert config.model is None
        assert config.fk_field == ""
        assert config.fields == []
        assert config.exclude == []
        assert config.readonly_fields == []
        assert config.extra == 3
        assert config.max_num is None
        assert config.min_num == 0
        assert config.can_delete is True
        assert config.verbose_name == ""
        assert config.verbose_name_plural == ""
        assert config.ordering == []

    def test_tabular_inline_template(self):
        """Test TabularInline has correct template."""
        from p8s.admin.inlines import TabularInline

        inline = TabularInline()
        assert inline.template == "tabular"

    def test_stacked_inline_template(self):
        """Test StackedInline has correct template."""
        from p8s.admin.inlines import StackedInline

        inline = StackedInline()
        assert inline.template == "stacked"


class TestInlineMetadata:
    """Test inline metadata extraction."""

    def test_get_inline_metadata_with_model_string(self):
        """Test get_inline_metadata with model as string."""
        from p8s.admin.inlines import TabularInline, get_inline_metadata

        inline = TabularInline()
        inline.model = "OrderItem"
        inline.fk_field = "order_id"
        inline.fields = ["product", "quantity", "price"]
        inline.extra = 1

        metadata = get_inline_metadata(inline)

        assert metadata["model"] == "OrderItem"
        assert metadata["fk_field"] == "order_id"
        assert metadata["template"] == "tabular"
        assert metadata["extra"] == 1
        assert len(metadata["fields"]) == 3

    def test_get_inline_metadata_empty_model(self):
        """Test get_inline_metadata with no model returns empty dict."""
        from p8s.admin.inlines import TabularInline, get_inline_metadata

        inline = TabularInline()
        inline.model = None

        metadata = get_inline_metadata(inline)

        assert metadata == {}

    def test_get_model_inlines_no_admin(self):
        """Test get_model_inlines returns empty list for models without Admin."""
        from p8s.admin.inlines import get_model_inlines

        # Create a simple mock class without Admin attribute
        class MockModel:
            pass

        result = get_model_inlines(MockModel)
        assert result == []

    def test_inline_verbose_names(self):
        """Test inline verbose name generation."""
        from p8s.admin.inlines import TabularInline, get_inline_metadata

        inline = TabularInline()
        inline.model = "OrderItem"
        inline.fk_field = "order_id"
        inline.verbose_name = "Item"
        inline.verbose_name_plural = "Items"

        metadata = get_inline_metadata(inline)

        assert metadata["verbose_name"] == "Item"
        assert metadata["verbose_name_plural"] == "Items"


class TestInlineConfiguration:
    """Test inline configuration options."""

    def test_inline_can_delete_default(self):
        """Test can_delete defaults to True."""
        from p8s.admin.inlines import TabularInline

        inline = TabularInline()
        assert inline.can_delete is True

    def test_inline_extra_forms(self):
        """Test extra empty forms configuration."""
        from p8s.admin.inlines import TabularInline

        inline = TabularInline()
        inline.extra = 5

        assert inline.extra == 5

    def test_inline_max_num(self):
        """Test max_num configuration."""
        from p8s.admin.inlines import StackedInline

        inline = StackedInline()
        inline.max_num = 10

        assert inline.max_num == 10

    def test_inline_min_num(self):
        """Test min_num configuration."""
        from p8s.admin.inlines import TabularInline

        inline = TabularInline()
        inline.min_num = 1

        assert inline.min_num == 1

    def test_inline_ordering(self):
        """Test ordering configuration."""
        from p8s.admin.inlines import TabularInline

        inline = TabularInline()
        inline.ordering = ["position", "-created_at"]

        assert inline.ordering == ["position", "-created_at"]

    def test_inline_readonly_fields(self):
        """Test readonly_fields configuration."""
        from p8s.admin.inlines import StackedInline

        inline = StackedInline()
        inline.readonly_fields = ["created_at", "updated_at"]

        assert "created_at" in inline.readonly_fields
        assert "updated_at" in inline.readonly_fields
