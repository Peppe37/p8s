# Forms

P8s provides Django-style form validation using Pydantic.

## Overview

Forms provide:
- **Validation** - Pydantic-powered data validation
- **Error handling** - Django-style error collection
- **ModelForm** - Auto-generated forms from models
- **Field types** - HTML rendering hints

## Basic Usage

```python
from p8s.forms import Form

class ContactForm(Form):
    name: str
    email: str
    message: str

# Validate data
form = ContactForm.from_data(request.form)
if form.is_valid():
    print(form.data)  # Validated dict
else:
    print(form.errors.all())  # {"name": ["Field required"]}
```

## Form API

### `Form.from_data(data)`

Create a form from raw data (dict, form submission, etc.).

```python
form = ContactForm.from_data({"name": "John", "email": "john@example.com"})
```

### `form.is_valid()`

Check if validation passed.

```python
if form.is_valid():
    # Process data
    send_email(form.data)
```

### `form.errors`

Access validation errors.

```python
form.errors.all()      # {"field": ["error1", "error2"]}
form.errors.get("name")  # ["Field required"]
```

### `form.data`

Get validated data as dict.

```python
validated = form.data  # {"name": "John", "email": "john@example.com"}
```

---

## Field Types

P8s provides field types with HTML rendering hints:

```python
from p8s.forms import (
    CharField,
    EmailField,
    IntegerField,
    FloatField,
    BooleanField,
    DateField,
    DateTimeField,
    ChoiceField,
    TextAreaField,
    HiddenField,
    PasswordField,
)
```

### CharField

```python
class MyForm(Form):
    name: str = CharField(
        max_length=100,
        min_length=2,
        placeholder="Your name",
        help_text="Enter your full name",
    )
```

### EmailField

```python
email: str = EmailField(placeholder="email@example.com")
```

### IntegerField / FloatField

```python
age: int = IntegerField(min_value=0, max_value=150)
price: float = FloatField(min_value=0, step=0.01)
```

### BooleanField

```python
active: bool = BooleanField(help_text="Is this item active?")
```

### ChoiceField

```python
status: str = ChoiceField(choices=[
    ("draft", "Draft"),
    ("published", "Published"),
    ("archived", "Archived"),
])
```

### TextAreaField

```python
description: str = TextAreaField(rows=10, placeholder="Enter description...")
```

### PasswordField

```python
password: str = PasswordField(min_length=8)
```

### HiddenField

```python
csrf_token: str = HiddenField(default="")
```

---

## ModelForm

Auto-generate forms from SQLModel models.

```python
from p8s.forms import ModelForm
from backend.models import Product

class ProductForm(ModelForm):
    class Meta:
        model = Product
        fields = ["name", "price", "description"]
        exclude = ["created_at"]  # Optional

# Create from data
form = ProductForm.from_data(request.form)
if form.is_valid():
    product = Product(**form.data)
    session.add(product)

# Pre-populate from instance
form = ProductForm.from_instance(existing_product)
```

### Meta Options

| Option    | Description                   |
| --------- | ----------------------------- |
| `model`   | The Model class               |
| `fields`  | List of fields or `"__all__"` |
| `exclude` | Fields to exclude             |

Note: `id`, `created_at`, `updated_at`, `deleted_at` are excluded by default.

---

## Getting Field Info

For rendering forms, get field metadata:

```python
fields = ContactForm.get_fields()
# {
#   "name": {"type": "text", "required": True, "label": "Name"},
#   "email": {"type": "email", "required": True, "label": "Email"},
# }
```

---

## FastAPI Integration

```python
from fastapi import APIRouter, Request
from p8s.forms import Form

router = APIRouter()

class LoginForm(Form):
    email: str
    password: str

@router.post("/login")
async def login(request: Request):
    form_data = await request.form()
    form = LoginForm.from_data(dict(form_data))

    if not form.is_valid():
        return {"errors": form.errors.all()}

    # Authenticate user
    user = await authenticate(form.data["email"], form.data["password"])
    return {"token": create_token(user)}
```

---

## CSRF Protection

Use with CSRFMiddleware for form protection:

```python
from p8s.middleware import CSRFMiddleware, get_csrf_token

# In your form template
token = get_csrf_token(request)
# <input type="hidden" name="csrf_token" value="{{ token }}">
```

See [Middleware](middleware.md) for CSRF configuration.
