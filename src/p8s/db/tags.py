"""
P8s Tag Field - Array of tags/keywords storage.

Example:
    ```python
    from p8s.db.tags import TagField

    class Article(Model, table=True):
        title: str
        tags: list[str] = TagField()
    ```
"""

from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field


def TagField(
    max_tags: int | None = None,
    separator: str = ",",
    default: Any = None,
    **kwargs: Any,
) -> Any:
    if default is None:
        default = []

    # ... (docstring) ...
    schema_extra = kwargs.pop("schema_extra", {})
    schema_extra.update(
        {
            "x-tags": True,
            "x-max-tags": max_tags,
            "x-separator": separator,
        }
    )

    return Field(
        default=default,
        sa_column=Column(JSON),
        schema_extra=schema_extra,
        **kwargs,
    )


def parse_tags(value: str | list, separator: str = ",") -> list[str]:
    """
    Parse tag input to list of strings.

    Args:
        value: Tags as string or list
        separator: Separator for string parsing

    Returns:
        List of normalized tag strings
    """
    if isinstance(value, list):
        return [str(t).strip().lower() for t in value if t]

    if not value:
        return []

    return [t.strip().lower() for t in value.split(separator) if t.strip()]


__all__ = ["TagField", "parse_tags"]
