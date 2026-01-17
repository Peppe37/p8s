"""
Tests for P8s i18n (internationalization) module.
"""

import pytest


class TestI18nCore:
    """Test core i18n functions."""

    def test_i18n_import(self):
        """Test i18n module can be imported."""
        from p8s import i18n

        assert i18n is not None

    def test_gettext_import(self):
        """Test gettext function can be imported."""
        from p8s.i18n import gettext

        assert gettext is not None

    def test_activate_import(self):
        """Test activate function can be imported."""
        from p8s.i18n import activate

        assert activate is not None

    def test_get_language_default(self):
        """Test default language is English."""
        from p8s.i18n import deactivate, get_language

        deactivate()  # Reset to default
        assert get_language() == "en"

    def test_activate_language(self):
        """Test language activation."""
        from p8s.i18n import activate, deactivate, get_language

        activate("it")
        assert get_language() == "it"

        activate("fr")
        assert get_language() == "fr"

        deactivate()  # Cleanup
        assert get_language() == "en"

    def test_gettext_returns_original(self):
        """Test gettext returns original when no translation available."""
        from p8s.i18n import activate, deactivate
        from p8s.i18n import gettext as _

        deactivate()
        message = _("Hello, World!")
        assert message == "Hello, World!"

    def test_underscore_alias(self):
        """Test _ is an alias for gettext."""
        from p8s.i18n import _, gettext

        assert _ is gettext


class TestNgettext:
    """Test plural translation functions."""

    def test_ngettext_import(self):
        """Test ngettext can be imported."""
        from p8s.i18n import ngettext

        assert ngettext is not None

    def test_ngettext_singular(self):
        """Test ngettext returns singular for n=1."""
        from p8s.i18n import deactivate, ngettext

        deactivate()
        result = ngettext("1 item", "{n} items", 1)
        assert result == "1 item"

    def test_ngettext_plural(self):
        """Test ngettext returns plural for n>1."""
        from p8s.i18n import deactivate, ngettext

        deactivate()
        result = ngettext("1 item", "{n} items", 5)
        assert result == "{n} items"


class TestPgettext:
    """Test context-based translations."""

    def test_pgettext_import(self):
        """Test pgettext can be imported."""
        from p8s.i18n import pgettext

        assert pgettext is not None

    def test_pgettext_returns_message(self):
        """Test pgettext returns original message when no translation."""
        from p8s.i18n import deactivate, pgettext

        deactivate()
        result = pgettext("month", "May")
        assert result == "May"


class TestLazyString:
    """Test lazy translation."""

    def test_lazy_string_import(self):
        """Test LazyString can be imported."""
        from p8s.i18n import LazyString

        assert LazyString is not None

    def test_gettext_lazy_import(self):
        """Test gettext_lazy can be imported."""
        from p8s.i18n import gettext_lazy

        assert gettext_lazy is not None

    def test_lazy_string_str(self):
        """Test LazyString converts to string."""
        from p8s.i18n import deactivate, gettext_lazy

        deactivate()
        lazy = gettext_lazy("Hello")
        assert str(lazy) == "Hello"

    def test_lazy_string_repr(self):
        """Test LazyString repr."""
        from p8s.i18n import gettext_lazy

        lazy = gettext_lazy("Test message")
        assert "LazyString" in repr(lazy)
        assert "Test message" in repr(lazy)


class TestLocaleMiddleware:
    """Test locale middleware."""

    def test_middleware_import(self):
        """Test LocaleMiddleware can be imported."""
        from p8s.i18n.middleware import LocaleMiddleware

        assert LocaleMiddleware is not None

    def test_parse_accept_language_simple(self):
        """Test parsing simple Accept-Language header."""
        from p8s.i18n.middleware import LocaleMiddleware

        middleware = LocaleMiddleware(app=None)
        languages = middleware.parse_accept_language("it")

        assert languages == ["it"]

    def test_parse_accept_language_with_quality(self):
        """Test parsing Accept-Language with quality values."""
        from p8s.i18n.middleware import LocaleMiddleware

        middleware = LocaleMiddleware(app=None)
        languages = middleware.parse_accept_language("en;q=0.8,it;q=0.9,fr;q=0.5")

        # Should be sorted by quality descending
        assert languages[0] == "it"
        assert languages[1] == "en"
        assert languages[2] == "fr"

    def test_parse_accept_language_with_region(self):
        """Test parsing Accept-Language with region codes."""
        from p8s.i18n.middleware import LocaleMiddleware

        middleware = LocaleMiddleware(app=None)
        languages = middleware.parse_accept_language("it-IT,it;q=0.9,en-US;q=0.8")

        # Should normalize to base language
        assert "it" in languages
        assert "en" in languages

    def test_get_language_from_request(self):
        """Test get_language_from_request utility."""
        from unittest.mock import MagicMock

        from p8s.i18n.middleware import get_language_from_request

        request = MagicMock()
        request.state.language = "it"

        assert get_language_from_request(request) == "it"

    def test_get_language_from_request_default(self):
        """Test get_language_from_request returns default."""
        from unittest.mock import MagicMock

        from p8s.i18n.middleware import get_language_from_request

        request = MagicMock(spec=[])
        request.state = MagicMock(spec=[])

        assert get_language_from_request(request) == "en"
