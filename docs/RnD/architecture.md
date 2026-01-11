# Architecture R&D

> **Status**: Reference\
> **Last Updated**: 2026-01-10

## P8s Framework Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                        P8s Application                          │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                     FastAPI Core                          │  │
│  │   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐    │  │
│  │   │ Routing │  │ OpenAPI │  │ Depends │  │ Starlette│   │  │
│  │   └─────────┘  └─────────┘  └─────────┘  └─────────┘    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   P8s Framework Layer                     │  │
│  │                                                            │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │  │
│  │  │  Admin   │  │   Auth   │  │   AI     │  │  Forms   │  │  │
│  │  │  Panel   │  │  JWT/    │  │ AIField  │  │ Pydantic │  │  │
│  │  │  React   │  │ Perms    │  │ Vector   │  │ ModelForm│  │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │  │
│  │                                                            │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │  │
│  │  │   DB     │  │ Signals  │  │Middleware│  │ Testing  │  │  │
│  │  │ SQLModel │  │ Hooks    │  │ CSRF/etc │  │ Helpers  │  │  │
│  │  │ Alembic  │  │          │  │          │  │          │  │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    CLI (Typer)                            │  │
│  │  dev | migrate | shell | check | dumpdata | ...           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
```

---

## Module Overview

### Core (`p8s/core/`)

| File          | Purpose                               |
| ------------- | ------------------------------------- |
| `settings.py` | Pydantic settings with nested configs |
| `app.py`      | P8sApp class extending FastAPI        |

### Database (`p8s/db/`)

| File            | Purpose                                             |
| --------------- | --------------------------------------------------- |
| `base.py`       | Model base class with UUID, timestamps, soft delete |
| `session.py`    | Async session management                            |
| `migrations.py` | Alembic wrapper with auto-detection                 |

### Auth (`p8s/auth/`)

| File              | Purpose                        |
| ----------------- | ------------------------------ |
| `models.py`       | User model with roles          |
| `security.py`     | Password hashing, JWT creation |
| `permissions.py`  | Permission/Group models        |
| `dependencies.py` | FastAPI dependencies           |

### Admin (`p8s/admin/`)

| File          | Purpose                       |
| ------------- | ----------------------------- |
| `site.py`     | AdminSite, ModelAdmin classes |
| `registry.py` | Model registration            |
| `router.py`   | API endpoints for admin panel |
| `frontend/`   | React admin SPA               |
| `actions.py`  | Bulk actions                  |

### AI (`p8s/ai/`)

| File               | Purpose                          |
| ------------------ | -------------------------------- |
| `fields.py`        | AIField, VectorField definitions |
| `processor.py`     | AI content generation            |
| `vector_search.py` | Similarity search                |

### Forms (`p8s/forms/`)

| File        | Purpose                     |
| ----------- | --------------------------- |
| `base.py`   | Form, ModelForm classes     |
| `fields.py` | Field types with HTML hints |

---

## Request Flow

```
Request
   │
   ▼
┌─────────────────┐
│   Middleware    │ ← Timing, CORS, CSRF, Security Headers
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Routing      │ ← FastAPI router matching
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Dependencies   │ ← get_session, get_current_user
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Handler      │ ← Your endpoint code
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   DB Session    │ ← Async SQLAlchemy
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Signals       │ ← Pre/post save hooks
└────────┬────────┘
         │
         ▼
Response
```

---

## Design Decisions

### Why SQLModel over Django ORM?

| Aspect               | Django ORM     | SQLModel |
| -------------------- | -------------- | -------- |
| Async                | Partial (3.1+) | Native   |
| Type hints           | Optional       | Required |
| Pydantic integration | None           | Built-in |
| FastAPI integration  | Manual         | Native   |

### Why React Admin over Django Admin?

| Aspect        | Django Admin    | React Admin    |
| ------------- | --------------- | -------------- |
| Frontend      | Server-rendered | SPA            |
| Customization | Templates       | Components     |
| API           | Coupled         | REST/decoupled |
| Modern UX     | Limited         | Full control   |

### Why Pydantic Settings over django.conf?

| Aspect     | Django settings | Pydantic Settings  |
| ---------- | --------------- | ------------------ |
| Validation | Runtime errors  | Startup validation |
| Types      | Dynamic         | Static             |
| Env vars   | django-environ  | Built-in           |
| Nesting    | Flat            | Hierarchical       |

---

## Extension Points

### Custom Middleware

```python
from p8s.middleware import Middleware

class RateLimitMiddleware(Middleware):
    async def process_request(self, request, call_next):
        # Your logic
        return await call_next(request)
```

### Custom Management Commands

```
backend/apps/myapp/management/commands/mycommand.py
```

```python
async def command():
    """Description."""
    # Your code
```

### Custom Admin Actions

```python
from p8s.admin.actions import admin_action

@admin_action(description="Approve selected")
async def approve_items(session, queryset):
    for item in queryset:
        item.approved = True
    return f"{len(queryset)} items approved"
```
