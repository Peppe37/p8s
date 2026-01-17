"""
P8s Code Field - Syntax-highlighted code storage.

Example:
    ```python
    from p8s.db.code import CodeField

    class Snippet(Model, table=True):
        title: str
        code: str = CodeField(language="python")
    ```
"""

from typing import Any

from sqlalchemy import Column, Text
from sqlmodel import Field


def CodeField(
    language: str | None = None,
    theme: str = "vs-dark",
    line_numbers: bool = True,
    default: Any = "",
    **kwargs: Any,
) -> Any:
    # ... (docstring) ...
    schema_extra = kwargs.pop("schema_extra", {})
    schema_extra.update(
        {
            "x-code": True,
            "x-language": language,
            "x-theme": theme,
            "x-line-numbers": line_numbers,
        }
    )

    return Field(
        default=default,
        sa_column=Column(Text),
        schema_extra=schema_extra,
        **kwargs,
    )


__all__ = ["CodeField"]
