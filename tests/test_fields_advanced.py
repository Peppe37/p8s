"""
Tests for P8s Advanced Fields.
"""

import pytest


class TestSlugField:
    """Test SlugField."""

    def test_field_import(self):
        """Test SlugField can be imported."""
        from p8s.db.slug import SlugField

        assert SlugField is not None

    def test_field_creation(self):
        """Test slug field exists and is callable."""
        from p8s.db.slug import SlugField

        # SlugField returns a Field - it's callable
        assert callable(SlugField)


class TestSlugify:
    """Test slugify function."""

    def test_slugify_import(self):
        """Test slugify can be imported."""
        from p8s.db.slug import slugify

        assert slugify is not None

    def test_slugify_basic(self):
        """Test basic slugification."""
        from p8s.db.slug import slugify

        assert slugify("Hello World") == "hello-world"

    def test_slugify_special_chars(self):
        """Test removing special characters."""
        from p8s.db.slug import slugify

        assert slugify("Hello! World?") == "hello-world"

    def test_slugify_unicode(self):
        """Test unicode handling."""
        from p8s.db.slug import slugify

        result = slugify("Café", allow_unicode=True)
        assert "caf" in result


class TestTagField:
    """Test TagField."""

    def test_field_import(self):
        """Test TagField can be imported."""
        from p8s.db.tags import TagField

        assert TagField is not None

    def test_field_creation(self):
        """Test tag field exists and is callable."""
        from p8s.db.tags import TagField

        assert callable(TagField)


class TestParseTags:
    """Test parse_tags function."""

    def test_parse_import(self):
        """Test parse_tags can be imported."""
        from p8s.db.tags import parse_tags

        assert parse_tags is not None

    def test_parse_string(self):
        """Test parsing comma-separated string."""
        from p8s.db.tags import parse_tags

        result = parse_tags("python, web, api")
        assert result == ["python", "web", "api"]

    def test_parse_list(self):
        """Test parsing list input."""
        from p8s.db.tags import parse_tags

        result = parse_tags(["Python", "WEB"])
        assert result == ["python", "web"]


class TestCodeField:
    """Test CodeField."""

    def test_field_import(self):
        """Test CodeField can be imported."""
        from p8s.db.code import CodeField

        assert CodeField is not None

    def test_field_creation(self):
        """Test code field exists and is callable."""
        from p8s.db.code import CodeField

        assert callable(CodeField)


class TestColorField:
    """Test ColorField."""

    def test_field_import(self):
        """Test ColorField can be imported."""
        from p8s.db.fields import ColorField

        assert ColorField is not None

    def test_field_creation(self):
        """Test color field exists and is callable."""
        from p8s.db.fields import ColorField

        assert callable(ColorField)


class TestExports:
    """Test module exports."""

    def test_slug_exports(self):
        """Test slug module exports."""
        from p8s.db.slug import __all__

        assert "SlugField" in __all__
        assert "slugify" in __all__

    def test_tags_exports(self):
        """Test tags module exports."""
        from p8s.db.tags import __all__

        assert "TagField" in __all__

    def test_code_exports(self):
        """Test code module exports."""
        from p8s.db.code import __all__

        assert "CodeField" in __all__
