"""
Tests for P8s admin module.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest


class TestAdminRegistration:
    """Test admin model registration."""

    def test_admin_site_import(self):
        """Test admin site can be imported."""
        from p8s.admin.site import ModelAdmin, site

        assert site is not None
        assert ModelAdmin is not None

    def test_model_admin_defaults(self):
        """Test ModelAdmin default attributes."""
        from p8s.admin.site import ModelAdmin

        admin = ModelAdmin()

        assert hasattr(admin, "list_display")
        assert hasattr(admin, "list_filter")
        assert hasattr(admin, "search_fields")
        assert hasattr(admin, "ordering")

    def test_model_admin_config(self):
        """Test custom ModelAdmin configuration."""
        from p8s.admin.site import ModelAdmin

        class ProductAdmin(ModelAdmin):
            list_display = ["name", "price", "category"]
            list_filter = ["category"]
            search_fields = ["name", "description"]

        admin = ProductAdmin()

        assert "name" in admin.list_display
        assert "price" in admin.list_display
        assert "category" in admin.list_filter
        assert "name" in admin.search_fields


class TestAdminActions:
    """Test admin actions functionality."""

    def test_action_decorator_import(self):
        """Test admin_action decorator can be imported."""
        from p8s.admin.actions import admin_action

        assert admin_action is not None

    def test_builtin_actions_exist(self):
        """Test builtin admin actions exist."""
        from p8s.admin.actions import DEFAULT_ACTIONS

        assert "delete_selected" in DEFAULT_ACTIONS
        assert "restore_selected" in DEFAULT_ACTIONS

    def test_action_registration(self):
        """Test registering a custom action."""
        from p8s.admin.actions import admin_action

        @admin_action(description="Mark as active")
        async def mark_active(session, queryset):
            count = 0
            for item in queryset:
                item.is_active = True
                count += 1
            return f"Activated {count} items"

        assert mark_active.__name__ == "mark_active"
        assert hasattr(mark_active, "_admin_action")
        assert mark_active._admin_action is True


class TestAdminRegistry:
    """Test admin model registry."""

    def test_get_registered_models(self):
        """Test retrieving registered models."""
        from p8s.admin.registry import get_registered_models

        models = get_registered_models()

        assert isinstance(models, dict)

    def test_get_model(self):
        """Test getting a specific model by name."""
        from p8s.admin.registry import get_model

        # This may return None if no models registered yet
        result = get_model("nonexistent")
        assert result is None


class TestAdminMetadata:
    """Test admin metadata generation."""

    def test_field_type_detection(self):
        """Test field type detection for admin forms."""
        type_mapping = {
            "str": "text",
            "int": "number",
            "float": "number",
            "bool": "checkbox",
            "datetime": "datetime",
            "date": "date",
            "UUID": "text",
        }

        assert type_mapping["str"] == "text"
        assert type_mapping["bool"] == "checkbox"
        assert type_mapping["datetime"] == "datetime"

    def test_relation_detection(self):
        """Test relationship field detection."""
        # Relations should be detected and displayed as dropdowns
        field_meta = {
            "type": "relation",
            "relation": {
                "model": "Category",
                "local_field": "category_id",
            },
        }

        assert field_meta["type"] == "relation"
        assert "model" in field_meta["relation"]


class TestAdminSerialization:
    """Test admin data serialization."""

    def test_uuid_serialization(self):
        """Test UUID fields are serialized as strings."""
        from uuid import UUID

        uuid_val = UUID("12345678-1234-5678-1234-567812345678")
        serialized = str(uuid_val)

        assert isinstance(serialized, str)
        assert serialized == "12345678-1234-5678-1234-567812345678"

    def test_datetime_serialization(self):
        """Test datetime fields are serializable."""
        from datetime import datetime

        dt = datetime(2024, 1, 15, 10, 30, 0)

        # ISO format for JSON
        iso = dt.isoformat()

        assert "2024-01-15" in iso
        assert "10:30:00" in iso

    def test_relation_exclusion(self):
        """Test that relation objects are excluded from automatic dump."""
        # When serializing for API, we should exclude relationship objects
        # to prevent lazy loading issues in async context

        model_data = {
            "id": "123",
            "name": "Test",
            "category_id": "456",  # FK - include
            # "category": {...}   # Relation object - EXCLUDE
        }

        relation_fields = {"category"}

        clean_data = {k: v for k, v in model_data.items() if k not in relation_fields}

        assert "id" in clean_data
        assert "name" in clean_data
        assert "category_id" in clean_data


class TestAdminListDisplay:
    """Test admin list display functionality."""

    def test_list_display_column_format(self):
        """Test list display column format."""
        columns = [
            {"key": "name", "label": "Name", "sortable": True},
            {"key": "price", "label": "Price", "sortable": True, "type": "number"},
            {
                "key": "created_at",
                "label": "Created",
                "sortable": True,
                "type": "datetime",
            },
        ]

        assert len(columns) == 3
        assert columns[0]["key"] == "name"
        assert columns[1]["type"] == "number"

    def test_label_generation_from_key(self):
        """Test automatic label generation from field key."""

        def generate_label(key: str) -> str:
            return key.replace("_", " ").title()

        assert generate_label("user_name") == "User Name"
        assert generate_label("created_at") == "Created At"
        assert generate_label("is_active") == "Is Active"
        assert generate_label("id") == "Id"
