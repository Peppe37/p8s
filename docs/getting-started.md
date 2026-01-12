# Getting Started with P8s

This guide will walk you through creating your first P8s application.

## Prerequisites

- Python 3.10+
- Node.js 18+ (for frontend)
- pip or uv package manager

## Installation

### Option 1: Install from source (recommended for development)

```bash
git clone https://github.com/Peppe37/p8s.git
cd p8s
pip install -e ".[all]"
```

### Option 2: Install from PyPI (coming soon)

```bash
pip install p8s
```

## Create a New Project

```bash
# Create a new P8s project
p8s new project myapp
cd myapp
```

This creates the following structure:

```
myapp/
├── backend/
│   ├── __init__.py
│   ├── main.py          # FastAPI application entry point
│   ├── models.py        # Your database models
│   └── settings.py      # Project configuration
├── frontend/            # React + Vite frontend
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── .env                 # Environment variables
└── pyproject.toml
```

## Run the Development Server

```bash
# Start both backend and frontend
p8s dev

# Or specify a port
p8s dev --port 8000

# Backend only (no frontend)
p8s dev --no-frontend
```

Output:
```
P8s (Prometheus)
━━━━━━━━━━━━━━━━━━━
Starting development server...
  Backend:  http://0.0.0.0:8000
  Frontend: http://localhost:5173

[backend] INFO: Uvicorn running on http://0.0.0.0:8000
[frontend] VITE ready in 500ms
```

## Access Your Application

| URL                            | Description                |
| ------------------------------ | -------------------------- |
| `http://localhost:8000`        | Backend API                |
| `http://localhost:8000/admin/` | Admin panel                |
| `http://localhost:8000/docs`   | OpenAPI docs (admin-only)  |
| `http://localhost:5173`        | Frontend (Vite dev server) |

## Create a Superuser

To access the admin panel, create a superuser:

```bash
p8s createsuperuser
# Email: admin@example.com
# Password: ****
```

## Create an App

Add a new app (e.g., `products`):

```bash
p8s new app products
```

This creates:

```
backend/apps/products/
├── __init__.py
├── models.py    # Database models
└── router.py    # API endpoints
```

Register the app in `backend/settings.py`:

```python
class AppSettings(Settings):
    installed_apps: list[str] = [
        "backend.apps.products",
    ]
```

## Next Steps

- [Models & Database](models.md) - Define your data models
- [Authentication](authentication.md) - User management and JWT
- [Admin Panel](admin.md) - Django-style admin interface
- [AI Features](ai.md) - AIField and VectorField
