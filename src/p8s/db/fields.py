"""
P8s Database Fields - Django-style field helpers for SQLModel.
"""

from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlmodel import Field as SQLModelField
from sqlmodel import Relationship as SQLModelRelationship
from sqlmodel import SQLModel

# Basic Types


def _process_args(kwargs: dict[str, Any]) -> dict[str, Any]:
    """Helper to map Django-style args to Pydantic/SQLModel."""
    if "verbose_name" in kwargs:
        kwargs["title"] = kwargs.pop("verbose_name")
    if "help_text" in kwargs:
        kwargs["description"] = kwargs.pop("help_text")
    return kwargs


def CharField(max_length: int = 255, **kwargs: Any) -> Any:
    """
    String field with fixed max length.

    Args:
        max_length: Maximum allowed length.
        **kwargs: Additional arguments for Field().
    """
    kwargs = _process_args(kwargs)
    return SQLModelField(sa_column=Column(String(max_length)), **kwargs)


def TextField(**kwargs: Any) -> Any:
    """
    Text field for unlimited length strings.
    """
    kwargs = _process_args(kwargs)
    return SQLModelField(sa_column=Column(Text), **kwargs)


def BooleanField(default: bool = False, **kwargs: Any) -> Any:
    """
    Boolean field.
    """
    kwargs = _process_args(kwargs)
    return SQLModelField(default=default, sa_column=Column(Boolean), **kwargs)


def IntegerField(default: int = 0, **kwargs: Any) -> Any:
    """
    Integer field.
    """
    kwargs = _process_args(kwargs)
    return SQLModelField(default=default, sa_column=Column(Integer), **kwargs)


def FloatField(default: float = 0.0, **kwargs: Any) -> Any:
    """
    Floating point number field.
    """
    kwargs = _process_args(kwargs)
    return SQLModelField(default=default, sa_column=Column(Float), **kwargs)


def DecimalField(
    max_digits: int = 10,
    decimal_places: int = 2,
    default: Decimal = Decimal("0"),
    **kwargs: Any,
) -> Any:
    """
    Decimal number field for currency etc.
    """
    kwargs = _process_args(kwargs)
    return SQLModelField(
        default=default,
        sa_column=Column(Numeric(precision=max_digits, scale=decimal_places)),
        **kwargs,
    )


# Date/Time


def DateField(auto_now: bool = False, auto_now_add: bool = False, **kwargs: Any) -> Any:
    """
    Date field.
    """
    kwargs = _process_args(kwargs)
    # Note: auto_now logic is typically handled by sa_column_kwargs or default_factory
    # SQLModel doesn't have direct auto_now support on Field like Django
    # We map it to sqlalchemy defaults/onupdate

    sa_kwargs = kwargs.pop("sa_column_kwargs", {})

    if auto_now:
        from sqlalchemy import func

        sa_kwargs["onupdate"] = func.now()

    if auto_now_add:
        # We use default_factory for creation time if not provided
        # But for DB level default we can use server_default
        pass

    # For simplicity in this helper we rely on standard Field usage or specific implementations
    # If the user wants auto behaviors they usually use the Model built-ins (created_at)
    # But to support Django-like args:

    if auto_now_add and "default_factory" not in kwargs:
        from datetime import date

        kwargs["default_factory"] = date.today

    return SQLModelField(sa_column=Column(Date), sa_column_kwargs=sa_kwargs, **kwargs)


def DateTimeField(
    auto_now: bool = False, auto_now_add: bool = False, **kwargs: Any
) -> Any:
    """
    DateTime field.
    """
    kwargs = _process_args(kwargs)
    if auto_now_add and "default_factory" not in kwargs:
        from datetime import datetime, timezone

        kwargs["default_factory"] = lambda: datetime.now(timezone.utc)

    return SQLModelField(sa_column=Column(DateTime), **kwargs)


# Structured / Validated


def JSONField(default: Any = None, **kwargs: Any) -> Any:
    """
    JSON field.
    """
    kwargs = _process_args(kwargs)
    if default is None:
        default = {}
    return SQLModelField(default=default, sa_column=Column(JSON), **kwargs)


def EmailField(**kwargs: Any) -> Any:
    """
    Email string field.
    Note: Requires type annotation to be EmailStr for validation alongside this Field.
    """
    kwargs = _process_args(kwargs)
    return SQLModelField(sa_column=Column(String(255)), **kwargs)


def URLField(**kwargs: Any) -> Any:
    """
    URL string field.
    """
    kwargs = _process_args(kwargs)
    return SQLModelField(sa_column=Column(String(2048)), **kwargs)


def ColorField(
    format: str = "hex",
    default: str = "#000000",
    **kwargs: Any,
) -> Any:
    """
    Color field for storing color values.

    Renders as color picker in admin UI.

    Args:
        format: Color format ("hex", "rgb", "hsl")
        default: Default color value
        **kwargs: Additional Field arguments

    Example:
        ```python
        class Theme(Model, table=True):
            primary_color: str = ColorField(default="#3B82F6")
            background: str = ColorField(format="rgb")
        ```
    """
    kwargs = _process_args(kwargs)
    json_schema_extra = kwargs.pop("json_schema_extra", {})
    json_schema_extra.update(
        {
            "x-color": True,
            "x-format": format,
        }
    )

    return SQLModelField(
        default=default,
        sa_column=Column(String(25)),
        json_schema_extra=json_schema_extra,
        **kwargs,
    )


# Relationships


def ForeignKey(
    to: type[SQLModel] | str, on_delete: str = "CASCADE", **kwargs: Any
) -> Any:
    """
    Foreign Key field.

    Args:
        to: Target model class or 'app.Model' string.
        on_delete: policies like CASCADE, SET NULL etc. (currently just passed)
    """
    kwargs = _process_args(kwargs)
    # If 'to' is a class, get its table name
    target = to
    if isinstance(to, type) and issubclass(to, SQLModel):
        target = getattr(to, "__tablename__", to.__name__.lower())

    # Assuming standard ID naming. This might be brittle if PK isn't 'id'
    target_col = f"{target}.id"

    return SQLModelField(foreign_key=target_col, **kwargs)


def ManyToManyField(
    to: type[SQLModel], link_model: type[SQLModel], **kwargs: Any
) -> Any:
    """
    Many-to-Many relationship.

    Args:
        to: Target model.
        link_model: The association table model.
    """
    # Relationship doesn't accept title/description like Field, so we ignore mapping
    return SQLModelRelationship(link_model=link_model, **kwargs)


def OneToOneField(to: type[SQLModel] | str, **kwargs: Any) -> Any:
    """
    One-to-One relationship (Foreign Key with Unique constraint).
    """
    # This is complex because logically it's a Field (FK) AND a Relationship usually in ORMs
    # In SQLModel, one-to-one is typically modeled as a unique Foreign Key

    kwargs["unique"] = True
    return ForeignKey(to, **kwargs)
