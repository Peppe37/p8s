"""
Tests for P8s database module.
"""

import pytest
from uuid import UUID
from datetime import datetime

from p8s.db.base import Model, AdminConfig


class TestModel:
    """Test base Model class."""

    def test_model_has_uuid_id(self):
        """Test that models have UUID primary key."""

        class TestItem(Model, table=True):
            __tablename__ = "test_items"
            name: str

        item = TestItem(name="test")

        assert item.id is not None
        assert isinstance(item.id, UUID)

    def test_model_has_timestamps(self):
        """Test that models have created_at and updated_at."""

        class TestItem(Model, table=True):
            __tablename__ = "test_items_ts"
            name: str

        item = TestItem(name="test")

        assert item.created_at is not None
        assert item.updated_at is not None
        assert isinstance(item.created_at, datetime)

    def test_soft_delete(self):
        """Test soft delete functionality."""

        class TestItem(Model, table=True):
            __tablename__ = "test_items_sd"
            name: str

        item = TestItem(name="test")

        assert item.is_deleted is False
        assert item.deleted_at is None

        item.soft_delete()

        assert item.is_deleted is True
        assert item.deleted_at is not None

    def test_restore(self):
        """Test restore after soft delete."""

        class TestItem(Model, table=True):
            __tablename__ = "test_items_restore"
            name: str

        item = TestItem(name="test")
        item.soft_delete()

        assert item.is_deleted is True

        item.restore()

        assert item.is_deleted is False
        assert item.deleted_at is None

    def test_to_dict(self):
        """Test model to dictionary conversion."""

        class TestItem(Model, table=True):
            __tablename__ = "test_items_dict"
            name: str

        item = TestItem(name="test")
        data = item.to_dict()

        assert "name" in data
        assert data["name"] == "test"
        assert "id" in data
        assert "created_at" in data

    def test_to_dict_with_exclude(self):
        """Test model to dict with excluded fields."""

        class TestItem(Model, table=True):
            __tablename__ = "test_items_exclude"
            name: str
            secret: str = "hidden"

        item = TestItem(name="test")
        data = item.to_dict(exclude={"secret"})

        assert "name" in data
        assert "secret" not in data


class TestAdminConfig:
    """Test Admin configuration."""

    def test_admin_config_defaults(self):
        """Test AdminConfig default values."""
        config = AdminConfig()

        assert config.list_display == []
        assert config.search_fields == []
        assert config.ordering == []

    def test_model_admin_config(self):
        """Test model with custom Admin config."""

        class Product(Model, table=True):
            __tablename__ = "products"
            name: str
            price: float

            class Admin:
                list_display = ["name", "price"]
                search_fields = ["name"]

        config = Product.get_admin_config()

        assert "name" in config.list_display
        assert "price" in config.list_display
        assert "name" in config.search_fields
