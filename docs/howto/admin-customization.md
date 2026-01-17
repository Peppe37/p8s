# How to Customize the Admin Panel

The P8s Admin Panel is a React-based SPA that auto-generates UI from your SQLModel classes.

## Basic Customization

Use the `Admin` nested class in your model:

```python
@register_model
class Product(SQLModel, table=True):
    # ... fields ...

    class Admin:
        name = "Merchandise"          # Custom display name
        plural_name = "Merchandise"
        list_display = ["name", "price", "stock"]
        search_fields = ["name", "sku"]
        list_filter = ["category", "is_active"]
        ordering = ["-created_at"]
        readonly_fields = ["created_at"]
```

## Custom Actions

Add custom buttons to the list view actions menu.

1.  Define the action function:

```python
from p8s.admin import action

@action(description="Mark as Out of Stock", confirm=True)
async def mark_out_of_stock(model, request, queryset):
    count = 0
    for item in queryset:
        item.stock = 0
        session.add(item)
        count += 1
    await session.commit()
    return {"message": f"Updated {count} products"}
```

2.  Register it in your model:

```python
from p8s.admin import register_action

@register_model
@register_action(mark_out_of_stock)
class Product(SQLModel, table=True):
    # ...
```

## Inline Models

Edit related models on the same page (e.g., Order Items inside an Order).

```python
class OrderItem(SQLModel, table=True):
    # ...
    order_id: int = Field(foreign_key="order.id")

class Order(SQLModel, table=True):
    # ...
    class Admin:
        inlines = [OrderItem]
```

## Custom Fields (RichText, Color, etc.)

Use specialized field types for enhanced UI:

```python
from p8s.db.fields import ColorField
from p8s.db.richtext import RichTextField

class Page(SQLModel, table=True):
    content: RichTextField  # Renders a WYSIWYG editor
    theme_color: ColorField # Renders a color picker
```
