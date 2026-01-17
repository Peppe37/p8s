# Admin Panel

P8s includes a Django-style admin panel for managing your data models.

## Overview

The admin panel provides:

- **CRUD operations** for all registered models
- **Search & filtering**
- **Pagination**
- **Bulk actions** (delete, export)
- **User authentication**

## Accessing the Admin

Navigate to:

```
http://localhost:8000/admin/
```

### Authentication

The admin panel requires authentication:

1. **Not logged in** → Shows login page
2. **Logged in as superuser** → Full access to dashboard
3. **Logged in as regular user** → "Invalid credentials" error

Create a superuser to access admin:

```bash
p8s createsuperuser
```

## Registering Models

Models appear in the admin automatically if they use `@register_model`:

```python
from p8s import Model
from p8s.admin import register_model
from sqlmodel import Field

@register_model
class Product(Model, table=True):
    name: str = Field(index=True)
    price: float
    is_active: bool = True

    class Admin:
        list_display = ["name", "price", "is_active"]
        search_fields = ["name"]
        list_filter = ["is_active"]
```

## Admin Configuration

Customize admin behavior with the inner `Admin` class:

### `list_display`

Fields shown in the list view:

```python
class Admin:
    list_display = ["name", "price", "created_at"]
```

### `search_fields`

Fields searchable via the search box:

```python
class Admin:
    search_fields = ["name", "description"]
```

### `list_filter`

Fields available for filtering:

```python
class Admin:
    list_filter = ["is_active", "category"]
```

### `ordering`

Default sort order:

```python
class Admin:
    ordering = ["-created_at"]  # Descending
```

### `readonly_fields`

Fields that cannot be edited:

```python
class Admin:
    readonly_fields = ["created_at", "updated_at"]
```

### Complete Example

```python
@register_model
class Article(Model, table=True):
    title: str
    content: str
    published: bool = False
    author_id: UUID | None = None

    class Admin:
        list_display = ["title", "published", "created_at"]
        search_fields = ["title", "content"]
        list_filter = ["published"]
        ordering = ["-created_at"]
        readonly_fields = ["created_at", "updated_at"]
```

## Admin API Endpoints

The admin exposes REST endpoints under `/admin/`:

| Method | Endpoint                     | Description            |
| ------ | ---------------------------- | ---------------------- |
| GET    | `/admin/`                    | Admin UI (HTML)        |
| GET    | `/admin/models`              | List registered models |
| GET    | `/admin/models/{name}`       | Model metadata         |
| GET    | `/admin/{model}`             | List records           |
| POST   | `/admin/{model}`             | Create record          |
| GET    | `/admin/{model}/{id}`        | Get record             |
| PATCH  | `/admin/{model}/{id}`        | Update record          |
| DELETE | `/admin/{model}/{id}`        | Delete record          |
| POST   | `/admin/{model}/bulk-delete` | Bulk delete            |

All API endpoints require admin authentication.

## Security

### Protected by default

- All admin endpoints require `require_admin` dependency
- Uses JWT Bearer token authentication
- OpenAPI docs (`/docs`) are also admin-protected

### CORS Configuration

Ensure your CORS settings allow the admin UI:

```python
class AppSettings(Settings):
    cors_origins: list[str] = ["http://localhost:8000"]
```

## Customizing the Admin

### Admin Settings

Configure admin behavior in `settings.py`:

```python
class AppSettings(Settings):
    admin: AdminSettings = AdminSettings(
        enabled=True,
        path="/admin",
        title="My App Admin",
    )
```

### Disabling Admin

```python
class AppSettings(Settings):
    admin: AdminSettings = AdminSettings(
        enabled=False,
    )
```
