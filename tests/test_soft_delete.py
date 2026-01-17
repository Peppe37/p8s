"""
Tests for P8s enhanced soft delete system.
"""

from datetime import datetime
from uuid import UUID

import pytest
from sqlmodel import Field, Relationship, select

from p8s.db.base import Model


class TestDeleteMethod:
    """Test the new delete(mode) method."""

    def test_delete_soft_default(self):
        """Test that delete() defaults to soft delete."""

        class TestSoftDeleteItem(Model, table=True):
            __tablename__ = "test_delete_soft"
            name: str

        item = TestSoftDeleteItem(name="test")

        assert item.is_deleted is False
        assert item.deleted_at is None

        item.delete()

        assert item.is_deleted is True
        assert item.deleted_at is not None

    def test_delete_soft_explicit(self):
        """Test delete(mode='soft') explicitly."""

        class TestItem(Model, table=True):
            __tablename__ = "test_delete_soft_explicit"
            name: str

        item = TestItem(name="test")
        item.delete(mode="soft")

        assert item.is_deleted is True
        assert item.deleted_at is not None

    def test_delete_hard(self):
        """Test delete(mode='hard') sets pending flag."""

        class TestItem(Model, table=True):
            __tablename__ = "test_delete_hard"
            name: str

        item = TestItem(name="test")
        item.delete(mode="hard")

        # Hard delete marks the item for deletion
        assert item._pending_hard_delete is True
        # Soft delete fields should NOT be touched
        assert item.deleted_at is None

    def test_delete_invalid_mode(self):
        """Test delete with invalid mode raises error."""

        class TestItem(Model, table=True):
            __tablename__ = "test_delete_invalid"
            name: str

        item = TestItem(name="test")

        with pytest.raises(ValueError) as exc_info:
            item.delete(mode="invalid")

        assert "Invalid delete mode" in str(exc_info.value)

    def test_delete_no_cascade(self):
        """Test delete with cascade=False."""

        class TestItem(Model, table=True):
            __tablename__ = "test_delete_no_cascade"
            name: str

        item = TestItem(name="test")
        # Should not raise even without cascade
        item.delete(cascade=False)

        assert item.is_deleted is True


class TestQueryHelpers:
    """Test the query helper class methods."""

    def test_active_returns_select(self):
        """Test that active() returns a Select statement."""

        class TestItem(Model, table=True):
            __tablename__ = "test_active_query"
            name: str

        stmt = TestItem.active()

        # Should be a SQLAlchemy Select statement
        assert hasattr(stmt, "where")
        # Check it filters by deleted_at
        assert "deleted_at" in str(stmt)

    def test_deleted_returns_select(self):
        """Test that deleted() returns a Select statement."""

        class TestItem(Model, table=True):
            __tablename__ = "test_deleted_query"
            name: str

        stmt = TestItem.deleted()

        assert hasattr(stmt, "where")
        assert "deleted_at" in str(stmt)

    def test_all_with_deleted_returns_select(self):
        """Test that all_with_deleted() returns a Select statement."""

        class TestItem(Model, table=True):
            __tablename__ = "test_all_query"
            name: str

        stmt = TestItem.all_with_deleted()

        assert hasattr(stmt, "where")

    def test_active_can_chain(self):
        """Test that active() can be chained with additional where."""

        class TestItem(Model, table=True):
            __tablename__ = "test_active_chain"
            name: str
            category: str = "default"

        stmt = TestItem.active().where(TestItem.category == "electronics")

        # Should have both conditions
        stmt_str = str(stmt)
        assert "deleted_at" in stmt_str
        assert "category" in stmt_str

    def test_deleted_can_chain(self):
        """Test that deleted() can be chained with order_by."""

        class TestItem(Model, table=True):
            __tablename__ = "test_deleted_chain"
            name: str

        stmt = TestItem.deleted().order_by(TestItem.created_at.desc())

        # Should work without error
        assert stmt is not None


class TestRestoreAfterDelete:
    """Test restore functionality after using delete()."""

    def test_restore_after_delete(self):
        """Test that restore() works after delete()."""

        class TestItem(Model, table=True):
            __tablename__ = "test_restore_delete"
            name: str

        item = TestItem(name="test")
        item.delete()

        assert item.is_deleted is True

        item.restore()

        assert item.is_deleted is False
        assert item.deleted_at is None


class TestModelIntegration:
    """Integration tests for soft delete with full model."""

    def test_model_has_all_delete_features(self):
        """Test that a Model has all soft delete features."""

        class Product(Model, table=True):
            __tablename__ = "products_sd"
            name: str
            price: float = 0.0

        # Check delete method exists
        assert hasattr(Product, "delete")

        # Check query helpers exist
        assert hasattr(Product, "active")
        assert hasattr(Product, "deleted")
        assert hasattr(Product, "all_with_deleted")

        # Check instance methods
        product = Product(name="Test", price=10.0)
        assert hasattr(product, "delete")
        assert hasattr(product, "soft_delete")
        assert hasattr(product, "restore")
        assert hasattr(product, "is_deleted")

    def test_query_helper_types(self):
        """Test that query helpers return proper types."""

        class Item(Model, table=True):
            __tablename__ = "items_types"
            name: str

        active_stmt = Item.active()
        deleted_stmt = Item.deleted()
        all_stmt = Item.all_with_deleted()

        # All should be Select statements
        from sqlalchemy.sql.selectable import Select

        assert isinstance(active_stmt, Select)
        assert isinstance(deleted_stmt, Select)
        assert isinstance(all_stmt, Select)
