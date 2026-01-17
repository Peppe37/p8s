"""
P8s Slug Field - Auto-generated URL-friendly slugs.

Example:
    ```python
    from p8s.db.slug import SlugField

    class Article(Model, table=True):
        title: str
        slug: str = SlugField(populate_from="title")
    ```
"""

import re
import unicodedata
from typing import Any

from sqlalchemy import String, Column
from sqlmodel import Field


def SlugField(
    populate_from: str | None = None,
    unique: bool = True,
    max_length: int = 255,
    allow_unicode: bool = False,
    **kwargs: Any,
) -> Any:
    """
    Create a slug field for URL-friendly identifiers.

    Args:
        populate_from: Field name to auto-generate slug from
        unique: Enforce unique slugs
        max_length: Maximum slug length
        allow_unicode: Allow unicode characters in slug
        **kwargs: Additional Field arguments

    Returns:
        SQLModel Field configured for slugs

    Example:
        ```python
        class Post(Model, table=True):
            title: str
            slug: str = SlugField(populate_from="title")

        # Auto-generates: "hello-world" from "Hello World!"
        ```
    """
    json_schema_extra = kwargs.pop("json_schema_extra", {})
    json_schema_extra.update({
        "x-slug": True,
        "x-populate-from": populate_from,
        "x-allow-unicode": allow_unicode,
    })

    return Field(
        default="",
        sa_column=Column(String(max_length), unique=unique, index=True),
        json_schema_extra=json_schema_extra,
        **kwargs,
    )


def slugify(value: str, allow_unicode: bool = False) -> str:
    """
    Convert a string to a URL-friendly slug.

    Args:
        value: String to convert
        allow_unicode: Keep unicode characters

    Returns:
        URL-friendly slug

    Examples:
        >>> slugify("Hello World!")
        "hello-world"
        >>> slugify("  Café Münster  ", allow_unicode=True)
        "café-münster"
    """
    value = str(value)

    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = (
            unicodedata.normalize("NFKD", value)
            .encode("ascii", "ignore")
            .decode("ascii")
        )

    value = value.lower().strip()
    value = re.sub(r"[^\w\s-]", "", value)
    value = re.sub(r"[-\s]+", "-", value)
    value = value.strip("-")

    return value


__all__ = ["SlugField", "slugify"]
