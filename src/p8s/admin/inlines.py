"""
P8s Admin Inlines - Django-style inline models for related object editing.

Provides:
- TabularInline for table-like editing of related objects
- StackedInline for stacked form editing
- Inline configuration and registry
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlmodel import SQLModel


@dataclass
class InlineConfig:
    """
    Configuration for an inline model.

    Example:
        ```python
        from p8s.admin.inlines import TabularInline

        class OrderItemInline(TabularInline):
            model = OrderItem
            fk_field = "order_id"
            fields = ["product_name", "quantity", "price"]
            extra = 1  # Number of empty forms to show
        ```
    """

    # The related model class
    model: type["SQLModel"] | None = None

    # Field name that references the parent model (FK field)
    fk_field: str = ""

    # Fields to display/edit
    fields: list[str] = field(default_factory=list)

    # Fields to exclude
    exclude: list[str] = field(default_factory=list)

    # Read-only fields
    readonly_fields: list[str] = field(default_factory=list)

    # Number of extra empty forms
    extra: int = 3

    # Maximum number of forms
    max_num: int | None = None

    # Minimum number of forms
    min_num: int = 0

    # Can delete inline items
    can_delete: bool = True

    # Verbose name
    verbose_name: str = ""
    verbose_name_plural: str = ""

    # Ordering
    ordering: list[str] = field(default_factory=list)


class TabularInline(InlineConfig):
    """
    Inline displayed as a table.

    Each related object is shown as a row in a table.

    Example:
        ```python
        class OrderItemInline(TabularInline):
            model = OrderItem
            fk_field = "order_id"
            fields = ["product_name", "quantity", "price"]
        ```
    """

    template: str = "tabular"


class StackedInline(InlineConfig):
    """
    Inline displayed as stacked forms.

    Each related object is shown as a separate form block.

    Example:
        ```python
        class OrderItemInline(StackedInline):
            model = OrderItem
            fk_field = "order_id"
            fields = ["product_name", "quantity", "price", "notes"]
        ```
    """

    template: str = "stacked"


def get_inline_metadata(inline: InlineConfig) -> dict[str, Any]:
    """
    Extract metadata from an inline configuration.

    Args:
        inline: InlineConfig instance.

    Returns:
        Metadata dictionary for the frontend.
    """
    model = inline.model
    if not model:
        return {}

    # Handle model as string (model name) - return minimal metadata
    if isinstance(model, str):
        return {
            "model": model,
            "fk_field": inline.fk_field,
            "fields": [{"name": f, "type": "str", "required": False, "readonly": False} 
                      for f in inline.fields] if inline.fields else [],
            "template": getattr(inline, "template", "tabular"),
            "extra": inline.extra,
            "max_num": inline.max_num,
            "min_num": inline.min_num,
            "can_delete": inline.can_delete,
            "verbose_name": inline.verbose_name or model,
            "verbose_name_plural": inline.verbose_name_plural or f"{model}s",
            "ordering": inline.ordering,
        }

    # Get field info from the model class
    fields = []
    for field_name, field_info in model.model_fields.items():
        # Skip if not in fields list (when fields specified)
        if inline.fields and field_name not in inline.fields:
            continue
        # Skip if in exclude list
        if field_name in inline.exclude:
            continue

        fields.append(
            {
                "name": field_name,
                "type": str(field_info.annotation),
                "required": field_info.is_required(),
                "readonly": field_name in inline.readonly_fields,
            }
        )

    return {
        "model": model.__name__,
        "fk_field": inline.fk_field,
        "fields": fields,
        "template": getattr(inline, "template", "tabular"),
        "extra": inline.extra,
        "max_num": inline.max_num,
        "min_num": inline.min_num,
        "can_delete": inline.can_delete,
        "verbose_name": inline.verbose_name or model.__name__,
        "verbose_name_plural": inline.verbose_name_plural or f"{model.__name__}s",
        "ordering": inline.ordering,
    }


def get_model_inlines(model: type["SQLModel"]) -> list[dict[str, Any]]:
    """
    Get inline configurations for a model.

    Args:
        model: The parent model class.

    Returns:
        List of inline metadata dictionaries.
    """
    if not hasattr(model, "Admin"):
        return []

    inlines = getattr(model.Admin, "inlines", [])
    return [get_inline_metadata(inline) for inline in inlines]
