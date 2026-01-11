"""
P8s Forms Fields - Field types with HTML rendering hints.

Each field type provides:
- Pydantic validation
- HTML input type hint
- Label generation
- Help text support
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any


@dataclass
class FieldInfo:
    """
    Field metadata for HTML rendering.

    Attributes:
        input_type: HTML input type (text, email, number, etc.)
        widget: Custom widget name for special rendering
        placeholder: Placeholder text
        help_text: Help text displayed below field
        min_value: Minimum value for number fields
        max_value: Maximum value for number fields
        min_length: Minimum length for text fields
        max_length: Maximum length for text fields
        choices: List of (value, label) tuples for select fields
        required: Whether field is required
        disabled: Whether field is disabled
        readonly: Whether field is readonly
        html_attrs: Additional HTML attributes
    """

    input_type: str = "text"
    widget: str | None = None
    placeholder: str | None = None
    help_text: str | None = None
    min_value: int | float | None = None
    max_value: int | float | None = None
    min_length: int | None = None
    max_length: int | None = None
    choices: list[tuple[Any, str]] | None = None
    required: bool = True
    disabled: bool = False
    readonly: bool = False
    html_attrs: dict[str, Any] = field(default_factory=dict)


def CharField(
    *,
    max_length: int | None = None,
    min_length: int | None = None,
    placeholder: str | None = None,
    help_text: str | None = None,
    required: bool = True,
    **kwargs,
) -> Any:
    """
    A text field.

    Example:
        name: str = CharField(max_length=100, placeholder="Your name")
    """
    from pydantic import Field as PydanticField

    field_info = FieldInfo(
        input_type="text",
        max_length=max_length,
        min_length=min_length,
        placeholder=placeholder,
        help_text=help_text,
        required=required,
        **kwargs,
    )

    return PydanticField(
        default=... if required else None,
        max_length=max_length,
        min_length=min_length,
        json_schema_extra={"field_info": field_info},
    )


def EmailField(
    *,
    placeholder: str | None = "email@example.com",
    help_text: str | None = None,
    required: bool = True,
    **kwargs,
) -> Any:
    """
    An email field with validation.

    Example:
        email: str = EmailField(placeholder="your@email.com")
    """
    from pydantic import Field as PydanticField

    field_info = FieldInfo(
        input_type="email",
        placeholder=placeholder,
        help_text=help_text,
        required=required,
        **kwargs,
    )

    return PydanticField(
        default=... if required else None,
        json_schema_extra={"field_info": field_info},
    )


def IntegerField(
    *,
    min_value: int | None = None,
    max_value: int | None = None,
    placeholder: str | None = None,
    help_text: str | None = None,
    required: bool = True,
    **kwargs,
) -> Any:
    """
    An integer field.

    Example:
        age: int = IntegerField(min_value=0, max_value=150)
    """
    from pydantic import Field as PydanticField

    field_info = FieldInfo(
        input_type="number",
        min_value=min_value,
        max_value=max_value,
        placeholder=placeholder,
        help_text=help_text,
        required=required,
        **kwargs,
    )

    return PydanticField(
        default=... if required else None,
        ge=min_value,
        le=max_value,
        json_schema_extra={"field_info": field_info},
    )


def FloatField(
    *,
    min_value: float | None = None,
    max_value: float | None = None,
    placeholder: str | None = None,
    help_text: str | None = None,
    required: bool = True,
    step: float = 0.01,
    **kwargs,
) -> Any:
    """
    A floating point field.

    Example:
        price: float = FloatField(min_value=0, step=0.01)
    """
    from pydantic import Field as PydanticField

    field_info = FieldInfo(
        input_type="number",
        min_value=min_value,
        max_value=max_value,
        placeholder=placeholder,
        help_text=help_text,
        required=required,
        html_attrs={"step": str(step)},
        **kwargs,
    )

    return PydanticField(
        default=... if required else None,
        ge=min_value,
        le=max_value,
        json_schema_extra={"field_info": field_info},
    )


def BooleanField(
    *,
    help_text: str | None = None,
    required: bool = False,
    **kwargs,
) -> Any:
    """
    A boolean/checkbox field.

    Example:
        active: bool = BooleanField(help_text="Is this item active?")
    """
    from pydantic import Field as PydanticField

    field_info = FieldInfo(
        input_type="checkbox",
        help_text=help_text,
        required=required,
        **kwargs,
    )

    return PydanticField(
        default=False,
        json_schema_extra={"field_info": field_info},
    )


def DateField(
    *,
    min_value: date | None = None,
    max_value: date | None = None,
    placeholder: str | None = None,
    help_text: str | None = None,
    required: bool = True,
    **kwargs,
) -> Any:
    """
    A date field.

    Example:
        birth_date: date = DateField()
    """
    from pydantic import Field as PydanticField

    field_info = FieldInfo(
        input_type="date",
        min_value=min_value,
        max_value=max_value,
        placeholder=placeholder,
        help_text=help_text,
        required=required,
        **kwargs,
    )

    return PydanticField(
        default=... if required else None,
        json_schema_extra={"field_info": field_info},
    )


def DateTimeField(
    *,
    min_value: datetime | None = None,
    max_value: datetime | None = None,
    placeholder: str | None = None,
    help_text: str | None = None,
    required: bool = True,
    **kwargs,
) -> Any:
    """
    A datetime field.

    Example:
        scheduled_at: datetime = DateTimeField()
    """
    from pydantic import Field as PydanticField

    field_info = FieldInfo(
        input_type="datetime-local",
        min_value=min_value,
        max_value=max_value,
        placeholder=placeholder,
        help_text=help_text,
        required=required,
        **kwargs,
    )

    return PydanticField(
        default=... if required else None,
        json_schema_extra={"field_info": field_info},
    )


def ChoiceField(
    *,
    choices: list[tuple[Any, str]],
    placeholder: str | None = "Select an option",
    help_text: str | None = None,
    required: bool = True,
    **kwargs,
) -> Any:
    """
    A select/dropdown field.

    Example:
        status: str = ChoiceField(choices=[
            ("draft", "Draft"),
            ("published", "Published"),
            ("archived", "Archived"),
        ])
    """
    from pydantic import Field as PydanticField

    field_info = FieldInfo(
        input_type="select",
        choices=choices,
        placeholder=placeholder,
        help_text=help_text,
        required=required,
        **kwargs,
    )

    return PydanticField(
        default=... if required else None,
        json_schema_extra={"field_info": field_info},
    )


def TextAreaField(
    *,
    max_length: int | None = None,
    min_length: int | None = None,
    placeholder: str | None = None,
    help_text: str | None = None,
    required: bool = True,
    rows: int = 5,
    **kwargs,
) -> Any:
    """
    A multiline text area field.

    Example:
        description: str = TextAreaField(rows=10, placeholder="Enter description...")
    """
    from pydantic import Field as PydanticField

    field_info = FieldInfo(
        input_type="textarea",
        widget="textarea",
        max_length=max_length,
        min_length=min_length,
        placeholder=placeholder,
        help_text=help_text,
        required=required,
        html_attrs={"rows": rows},
        **kwargs,
    )

    return PydanticField(
        default=... if required else None,
        max_length=max_length,
        min_length=min_length,
        json_schema_extra={"field_info": field_info},
    )


def HiddenField(
    *,
    default: Any = None,
    **kwargs,
) -> Any:
    """
    A hidden field.

    Example:
        csrf_token: str = HiddenField()
    """
    from pydantic import Field as PydanticField

    field_info = FieldInfo(
        input_type="hidden",
        required=False,
        **kwargs,
    )

    return PydanticField(
        default=default,
        json_schema_extra={"field_info": field_info},
    )


def PasswordField(
    *,
    min_length: int = 8,
    max_length: int | None = None,
    placeholder: str | None = "Enter password",
    help_text: str | None = None,
    required: bool = True,
    **kwargs,
) -> Any:
    """
    A password field (masked input).

    Example:
        password: str = PasswordField(min_length=12)
    """
    from pydantic import Field as PydanticField

    field_info = FieldInfo(
        input_type="password",
        min_length=min_length,
        max_length=max_length,
        placeholder=placeholder,
        help_text=help_text,
        required=required,
        **kwargs,
    )

    return PydanticField(
        default=... if required else None,
        min_length=min_length,
        max_length=max_length,
        json_schema_extra={"field_info": field_info},
    )
