"""
Tests for P8s Testing Factory.
"""

import pytest


class TestFieldGenerator:
    """Test FieldGenerator."""

    def test_string(self):
        """Test string generation."""
        from p8s.testing.factory import FieldGenerator

        s = FieldGenerator.string(10)
        assert len(s) == 10

    def test_string_with_prefix(self):
        """Test string with prefix."""
        from p8s.testing.factory import FieldGenerator

        s = FieldGenerator.string(5, prefix="user_")
        assert s.startswith("user_")

    def test_email(self):
        """Test email generation."""
        from p8s.testing.factory import FieldGenerator

        email = FieldGenerator.email()
        assert "@" in email

    def test_integer(self):
        """Test integer generation."""
        from p8s.testing.factory import FieldGenerator

        n = FieldGenerator.integer(10, 20)
        assert 10 <= n <= 20

    def test_float(self):
        """Test float generation."""
        from p8s.testing.factory import FieldGenerator

        f = FieldGenerator.float_(1.0, 10.0)
        assert 1.0 <= f <= 10.0

    def test_boolean(self):
        """Test boolean generation."""
        from p8s.testing.factory import FieldGenerator

        b = FieldGenerator.boolean()
        assert isinstance(b, bool)

    def test_uuid(self):
        """Test UUID generation."""
        from p8s.testing.factory import FieldGenerator

        uid = FieldGenerator.uuid()
        assert len(uid) == 36
        assert "-" in uid

    def test_name(self):
        """Test name generation."""
        from p8s.testing.factory import FieldGenerator

        name = FieldGenerator.name()
        assert " " in name

    def test_choice(self):
        """Test choice."""
        from p8s.testing.factory import FieldGenerator

        options = ["a", "b", "c"]
        result = FieldGenerator.choice(options)
        assert result in options


class TestLazy:
    """Test lazy attribute."""

    def test_lazy_import(self):
        """Test lazy can be imported."""
        from p8s.testing.factory import lazy

        assert lazy is not None

    def test_lazy_decorator(self):
        """Test lazy decorator."""
        from p8s.testing.factory import lazy, LazyAttribute

        @lazy
        def gen_name(_):
            return "Test"

        assert isinstance(gen_name, LazyAttribute)


class TestModelFactory:
    """Test ModelFactory."""

    def test_factory_import(self):
        """Test ModelFactory can be imported."""
        from p8s.testing.factory import ModelFactory

        assert ModelFactory is not None

    def test_build_with_static_values(self):
        """Test building with static values."""
        from p8s.testing.factory import ModelFactory

        class TestFactory(ModelFactory):
            name = "Test"
            value = 42

        data = TestFactory.build()
        assert data["name"] == "Test"
        assert data["value"] == 42

    def test_build_with_overrides(self):
        """Test building with overrides."""
        from p8s.testing.factory import ModelFactory

        class TestFactory(ModelFactory):
            name = "Default"

        data = TestFactory.build(name="Override")
        assert data["name"] == "Override"

    def test_build_with_lazy(self):
        """Test building with lazy attributes."""
        from p8s.testing.factory import ModelFactory, lazy

        class TestFactory(ModelFactory):
            uid = lazy(lambda _: "generated")

        data = TestFactory.build()
        assert data["uid"] == "generated"


class TestExports:
    """Test module exports."""

    def test_all_exports(self):
        """Test __all__ exports."""
        from p8s.testing.factory import __all__

        assert "ModelFactory" in __all__
        assert "FieldGenerator" in __all__
        assert "lazy" in __all__
