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

from sqlalchemy import Text, Column
from sqlmodel import Field


def CodeField(
    language: str | None = None,
    theme: str = "vs-dark",
    line_numbers: bool = True,
    **kwargs: Any,
) -> Any:
    """
    Create a code field for storing code snippets.

    Renders with syntax highlighting editor in admin.

    Args:
        language: Programming language for syntax highlighting
        theme: Editor theme (for Monaco editor)
        line_numbers: Show line numbers
        **kwargs: Additional Field arguments

    Returns:
        SQLModel Field configured for code storage

    Example:
        ```python
        class Template(Model, table=True):
            name: str
            html: str = CodeField(language="html")
            css: str = CodeField(language="css")
        ```
    """
    json_schema_extra = kwargs.pop("json_schema_extra", {})
    json_schema_extra.update({
        "x-code": True,
        "x-language": language,
        "x-theme": theme,
        "x-line-numbers": line_numbers,
    })

    return Field(
        default="",
        sa_column=Column(Text),
        json_schema_extra=json_schema_extra,
        **kwargs,
    )


__all__ = ["CodeField"]
