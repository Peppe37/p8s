<p align="center">
  <h1 align="center">P8s (Prometheus)</h1>
  <p align="center">
    <strong>Forge AI-native, full-stack applications with the fire of the gods.</strong>
  </p>
</p>

<p align="center">
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10+-blue?style=flat-square" alt="Python 3.10+"></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-async-009688?style=flat-square" alt="FastAPI"></a>
  <a href="https://react.dev/"><img src="https://img.shields.io/badge/React-Vite-61DAFB?style=flat-square" alt="React"></a>
  <a href="#"><img src="https://img.shields.io/badge/AI-Native-orange?style=flat-square" alt="AI Native"></a>
  <a href="https://github.com/Peppe37/p8s/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License"></a>
</p>

<p align="center">
  <a href="https://peppe37.github.io/p8s/getting-started/">Getting Started</a> •
  <a href="https://peppe37.github.io/p8s/">Documentation</a> •
  <a href="#features">Features</a> •
  <a href="#quick-start">Quick Start</a>
</p>

---

## Why P8s?

| Django              | FastAPI             | **P8s**                |
| ------------------- | ------------------- | ---------------------- |
| Complete but legacy | Fast but fragmented | **Best of both**       |
| Sync-first          | Async-first         | **Async by default**   |
| Admin included      | No admin            | **Django-style admin** |
| No AI support       | No AI support       | **AI is a primitive**  |

**P8s brings order to modern Python development.**

---

## Features

### Async Backend
- **FastAPI** under the hood
- **SQLModel** ORM (SQLAlchemy + Pydantic)
- **Automatic CRUD** for registered models
- **UUID & Soft Deletes** by default (`.active()`, `.deleted()`, `.all_with_deleted()`)

### Authentication
- **JWT Authentication** out of the box
- **User roles** (User, Admin, Superuser)
- **Permissions & Groups** (Django-style)
- **Secure defaults** (bcrypt, protected routes)

### AI-Native
- **AIField**: Auto-generate content from prompts
- **VectorField**: Store embeddings for semantic search
- **VectorSearch**: Query by similarity
- Supports **OpenAI**, **Anthropic**, **Google**, **Ollama**, and more

### Admin Panel
- **Django-style** admin interface
- **Dynamic CRUD** from your models
- **Search, filter, paginate, bulk actions**
- **No frontend code required**

### Forms & Validation
- **Pydantic-based** form validation
- **ModelForm** auto-generated from models
- **11 field types** with HTML rendering hints
- **CSRF protection** middleware

### Database & Migrations
- **Auto-detected migrations** with Alembic
- **Fixtures**: `dumpdata` / `loaddata`
- **Database shell**: `dbshell`

### CLI Tools (18+ commands)

```bash
p8s new project myapp    # Create project
p8s new app blog         # Add app
p8s dev                  # Development server (backend + frontend)
p8s migrate              # Run migrations
p8s makemigrations       # Auto-detect model changes
p8s createsuperuser      # Create admin user
p8s shell                # Interactive Python shell
p8s check                # Validate configuration
p8s dumpdata             # Export fixtures
p8s loaddata             # Import fixtures
p8s dbshell              # Database shell
p8s sendtestemail        # Test email config
p8s collectstatic        # Collect static files
```

---

## Quick Start

### Installation

```bash
pip install p8s
```

### Create a Project

```bash
p8s new project myapp
cd myapp
```

### Run Development Server

```bash
p8s dev
```

```
P8s (Prometheus)
━━━━━━━━━━━━━━━━━━━
Starting development server...
  Backend:  http://localhost:8000
  Frontend: http://localhost:5173

[backend] INFO: Uvicorn running on http://localhost:8000
[frontend] VITE ready in 456ms
```

### Access Your App

| URL                            | Description  |
| ------------------------------ | ------------ |
| `http://localhost:8000`        | Backend API  |
| `http://localhost:8000/admin/` | Admin panel  |
| `http://localhost:8000/docs`   | OpenAPI docs |
| `http://localhost:5173`        | Frontend     |

---

## Code Example

```python
from p8s import Model
from p8s.ai import AIField, VectorField
from p8s.admin import register_model
from sqlmodel import Field

@register_model
class Product(Model, table=True):
    name: str = Field(index=True)
    description: str

    # AI-generated SEO description
    seo_description: str | None = AIField(
        prompt="Generate SEO description for {name}: {description}",
        source_fields=["name", "description"],
    )

    # Vector embedding for similarity search
    embedding: list[float] | None = VectorField(
        source_field="description"
    )

    class Admin:
        list_display = ["name", "created_at"]
        search_fields = ["name"]
```

### Forms Example

```python
from p8s.forms import Form, ModelForm, CharField, EmailField

class ContactForm(Form):
    name: str = CharField(max_length=100)
    email: str = EmailField()
    message: str

form = ContactForm.from_data(request.form)
if form.is_valid():
    send_email(form.data)
```

---

## Project Structure

```
myapp/
├── backend/
│   ├── main.py          # FastAPI entry point
│   ├── models.py        # Database models
│   ├── settings.py      # Configuration (Pydantic Settings)
│   └── apps/            # Your apps
│       └── products/
│           ├── models.py
│           ├── router.py
│           └── schemas.py
├── frontend/            # React + Vite
│   └── src/
├── migrations/          # Alembic migrations
└── .env                 # Environment variables
```

---

## Documentation

| Topic                                                             | Description                  |
| ----------------------------------------------------------------- | ---------------------------- |
| [Getting Started](https://peppe37.github.io/p8s/getting-started/) | Create your first project    |
| [CLI Reference](https://peppe37.github.io/p8s/cli/)               | All 18+ commands             |
| [Models & Database](https://peppe37.github.io/p8s/models/)        | SQLModel ORM usage           |
| [Migrations](https://peppe37.github.io/p8s/migrations/)           | Auto-detected migrations     |
| [Authentication](https://peppe37.github.io/p8s/authentication/)   | JWT and user management      |
| [Admin Panel](https://peppe37.github.io/p8s/admin/)               | Django-style admin           |
| [Forms](https://peppe37.github.io/p8s/forms/)                     | Validation & ModelForm       |
| [Middleware](https://peppe37.github.io/p8s/middleware/)           | CSRF, security, timing       |
| [AI Features](https://peppe37.github.io/p8s/ai/)                  | AIField, VectorField, search |
| [Testing](https://peppe37.github.io/p8s/testing/)                 | Test utilities               |
| [Configuration](https://peppe37.github.io/p8s/configuration/)     | Environment and settings     |
| [Deployment](https://peppe37.github.io/p8s/deployment/)           | Docker, Railway, Fly.io      |

---

## Test Coverage

```bash
pytest tests/ -v
# 186 passed
```

---

## Roadmap

### Completed
- [x] Django-style settings discovery (`P8S_SETTINGS_MODULE`)
- [x] Admin panel with login, CRUD, bulk actions
- [x] JWT authentication with permissions/groups
- [x] SQLModel integration with soft deletes
- [x] **Alembic migrations** with auto-detection
- [x] **Forms module** with ModelForm
- [x] **CSRF middleware**
- [x] **Fixtures** (dumpdata/loaddata)
- [x] **Testing utilities**
- [x] **186 tests passing**

### In Progress
- [ ] Admin inlines (nested models)
- [ ] Frontend auth hooks
- [ ] TypeScript type generation

### Planned
- [ ] WebSocket support
- [ ] Background tasks (Celery/ARQ)
- [ ] i18n/l10n
- [ ] Multi-tenancy
- [ ] GraphQL support
- [ ] PyPI release

---

## Contributing

Contributions are welcome! Please read the contributing guidelines before submitting a PR.

```bash
# Run tests
pytest tests/

# Lint
ruff check src/

# Format
ruff format src/
```

---

## License

MIT — steal the fire, responsibly

---

<p align="center">
  <sub>Built with ❤️ by Peppe37</sub>
</p>
