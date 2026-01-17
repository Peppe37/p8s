"""
Tests for P8s application core module.
"""

from unittest.mock import MagicMock, patch

import pytest


class TestP8sAppImport:
    """Test P8sApp class."""

    def test_p8s_app_import(self):
        """Test P8sApp can be imported."""
        from p8s import P8sApp

        assert P8sApp is not None

    def test_p8s_version(self):
        """Test P8s version is defined."""
        from p8s import __version__

        assert __version__ is not None
        assert isinstance(__version__, str)
        # Should follow semver format x.y.z
        parts = __version__.split(".")
        assert len(parts) >= 2


class TestSettings:
    """Test Settings configuration."""

    def test_settings_import(self):
        """Test Settings can be imported."""
        from p8s import Settings

        assert Settings is not None

    def test_settings_defaults(self):
        """Test Settings has sensible defaults."""
        from p8s.core.settings import Settings

        settings = Settings()

        assert settings.debug is False  # Default should be False for safety
        assert settings.secret_key is not None

    def test_admin_settings(self):
        """Test AdminSettings configuration."""
        from p8s.core.settings import AdminSettings

        admin = AdminSettings()

        assert hasattr(admin, "title")
        assert admin.title == "P8s Admin"  # Default

    def test_database_settings(self):
        """Test DatabaseSettings configuration."""
        from p8s.core.settings import DatabaseSettings

        db = DatabaseSettings()

        assert hasattr(db, "url")
        assert hasattr(db, "echo")


class TestExports:
    """Test main module exports."""

    def test_all_core_exports(self):
        """Test all core exports are available."""
        from p8s import (
            Model,
            P8sApp,
            Settings,
            Signal,
            get_session,
            receiver,
        )

        assert P8sApp is not None
        assert Settings is not None
        assert Model is not None
        assert get_session is not None
        assert Signal is not None
        assert receiver is not None

    def test_auth_exports(self):
        """Test auth exports are available."""
        from p8s import Group, Permission

        assert Permission is not None
        assert Group is not None

    def test_storage_exports(self):
        """Test storage exports are available."""
        from p8s import FileField, ImageField

        assert FileField is not None
        assert ImageField is not None

    def test_field_exports(self):
        """Test field exports are available."""
        from p8s import (
            BooleanField,
            CharField,
            DateField,
            DateTimeField,
            FloatField,
            IntegerField,
            JSONField,
            TextField,
        )

        # All should be importable
        assert CharField is not None
        assert TextField is not None
        assert BooleanField is not None
        assert IntegerField is not None

    def test_ai_exports(self):
        """Test AI exports are available (optional)."""
        from p8s import AIField, VectorField

        # These might be None if AI dependencies not installed
        # Just test they're exported without error
        assert True  # Import succeeded


class TestApplicationLifecycle:
    """Test application lifecycle events."""

    def test_app_has_lifespan_hooks(self):
        """Test P8sApp has lifespan hooks."""
        from p8s import P8sApp

        app = P8sApp(title="Test App")

        # FastAPI app should have lifespan
        assert hasattr(app, "router")
        assert hasattr(app, "add_event_handler")

    def test_app_routes_registration(self):
        """Test routes can be registered."""
        from p8s import P8sApp

        app = P8sApp(title="Test App")

        @app.get("/test")
        async def test_route():
            return {"status": "ok"}

        # Route should be registered
        routes = [r.path for r in app.routes]
        assert "/test" in routes


class TestRouting:
    """Test routing utilities."""

    def test_include_router(self):
        """Test including routers."""
        from fastapi import APIRouter

        from p8s import P8sApp

        app = P8sApp(title="Test App")
        router = APIRouter(prefix="/api")

        @router.get("/items")
        async def get_items():
            return []

        app.include_router(router)

        routes = [r.path for r in app.routes]
        assert "/api/items" in routes
