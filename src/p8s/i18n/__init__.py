"""
P8s Internationalization (i18n) Module.

Provides Django-style internationalization support:
- gettext for translations
- Language activation and detection
- Locale middleware integration

Example:
    ```python
    from p8s.i18n import gettext as _, activate, get_language

    activate("it")
    message = _("Welcome to our store")  # Returns translated string
    ```
"""

import gettext as python_gettext
import os
from collections.abc import Callable
from contextvars import ContextVar
from pathlib import Path

# Context variable for current language
_current_language: ContextVar[str] = ContextVar("current_language", default="en")

# Loaded translation catalogs
_translations: dict[
    str, python_gettext.GNUTranslations | python_gettext.NullTranslations
] = {}

# Default locale directory
_locale_dir: Path | None = None


def configure(locale_dir: str | Path) -> None:
    """
    Configure the locale directory for translations.

    Args:
        locale_dir: Path to the locale directory containing .mo files.
                   Structure: locale_dir/{language}/LC_MESSAGES/{domain}.mo
    """
    global _locale_dir
    _locale_dir = Path(locale_dir)


def get_language() -> str:
    """
    Get the current active language.

    Returns:
        Current language code (e.g., 'en', 'it', 'fr')
    """
    return _current_language.get()


def activate(language: str) -> None:
    """
    Activate a language for the current context.

    Args:
        language: Language code to activate (e.g., 'it', 'fr', 'de')

    Example:
        ```python
        from p8s.i18n import activate, gettext as _

        activate("it")
        print(_("Hello"))  # Prints Italian translation
        ```
    """
    _current_language.set(language)


def deactivate() -> None:
    """Reset to default language."""
    _current_language.set("en")


def get_translation(
    language: str, domain: str = "messages"
) -> python_gettext.GNUTranslations | python_gettext.NullTranslations:
    """
    Get a translation catalog for a language.

    Args:
        language: Language code
        domain: Translation domain (default: 'messages')

    Returns:
        Translation catalog
    """
    cache_key = f"{language}:{domain}"

    if cache_key not in _translations:
        if _locale_dir and _locale_dir.exists():
            try:
                _translations[cache_key] = python_gettext.translation(
                    domain,
                    localedir=str(_locale_dir),
                    languages=[language],
                )
            except FileNotFoundError:
                _translations[cache_key] = python_gettext.NullTranslations()
        else:
            _translations[cache_key] = python_gettext.NullTranslations()

    return _translations[cache_key]


def gettext(message: str) -> str:
    """
    Translate a message to the current language.

    This is the main translation function, commonly imported as _.

    Args:
        message: Message to translate

    Returns:
        Translated message, or original if no translation found

    Example:
        ```python
        from p8s.i18n import gettext as _

        welcome = _("Welcome to our store")
        ```
    """
    language = get_language()
    translation = get_translation(language)
    return translation.gettext(message)


def ngettext(singular: str, plural: str, n: int) -> str:
    """
    Translate a message with plural forms.

    Args:
        singular: Singular form of the message
        plural: Plural form of the message
        n: Number to determine which form to use

    Returns:
        Translated message in appropriate form

    Example:
        ```python
        from p8s.i18n import ngettext

        msg = ngettext("{n} item", "{n} items", count)
        ```
    """
    language = get_language()
    translation = get_translation(language)
    return translation.ngettext(singular, plural, n)


def pgettext(context: str, message: str) -> str:
    """
    Translate a message with context disambiguation.

    Args:
        context: Context string to disambiguate translations
        message: Message to translate

    Returns:
        Translated message

    Example:
        ```python
        from p8s.i18n import pgettext

        # Different translations for "May" as month vs verb
        month = pgettext("month", "May")
        verb = pgettext("verb", "May")
        ```
    """
    language = get_language()
    translation = get_translation(language)
    # Construct context-prefixed message
    msg_with_context = f"{context}\x04{message}"
    result = translation.gettext(msg_with_context)
    # If no translation, return original message
    if result == msg_with_context:
        return message
    return result


# Convenience alias
_ = gettext


# Lazy translation for use in class/module level definitions
class LazyString:
    """
    Lazy string that delays translation until accessed.

    Useful for strings defined at module level that need
    to be translated based on runtime language.
    """

    def __init__(self, func: Callable[[], str], message: str):
        self._func = func
        self._message = message

    def __str__(self) -> str:
        return self._func(self._message)

    def __repr__(self) -> str:
        return f"LazyString({self._message!r})"


def gettext_lazy(message: str) -> LazyString:
    """
    Mark a string for lazy translation.

    The translation happens when the string is accessed, not when defined.
    Useful for class-level or module-level string definitions.

    Args:
        message: Message to translate lazily

    Returns:
        LazyString that translates when converted to str

    Example:
        ```python
        from p8s.i18n import gettext_lazy as _

        class MyModel:
            verbose_name = _("Product")  # Translated on access
        ```
    """
    return LazyString(gettext, message)


# Export all public functions
__all__ = [
    "configure",
    "get_language",
    "activate",
    "deactivate",
    "gettext",
    "ngettext",
    "pgettext",
    "gettext_lazy",
    "_",
    "LazyString",
]
