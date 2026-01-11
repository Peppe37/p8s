# P8s Framework Documentation

Welcome to the **P8s (Prometheus)** documentation. Build AI-native, full-stack applications with the fire of the gods 🔥

## Core Documentation

| Topic                                 | Description                   |
| ------------------------------------- | ----------------------------- |
| [Getting Started](getting-started.md) | Create your first P8s project |
| [CLI Reference](cli.md)               | All available commands (18+)  |
| [Configuration](configuration.md)     | Settings and environment      |

## Features

| Topic                               | Description                  |
| ----------------------------------- | ---------------------------- |
| [Models & Database](models.md)      | SQLModel ORM, migrations     |
| [Migrations](migrations.md)         | Auto-detected migrations     |
| [Authentication](authentication.md) | JWT, users, permissions      |
| [Admin Panel](admin.md)             | Django-style admin interface |
| [Forms](forms.md)                   | Pydantic forms, validation   |
| [Middleware](middleware.md)         | CSRF, security, timing       |
| [Signals](signals.md)               | Model lifecycle hooks        |
| [Email](email.md)                   | Sending emails               |
| [Cache](cache.md)                   | Caching layer                |
| [Static Files](staticfiles.md)      | Static file handling         |

## AI Features

| Topic                         | Description                      |
| ----------------------------- | -------------------------------- |
| [AI Integration](ai.md)       | AIField, VectorField, embeddings |
| [Permissions](permissions.md) | Groups and permissions           |

## Development

| Topic                       | Description                |
| --------------------------- | -------------------------- |
| [Testing](testing.md)       | Test utilities and helpers |
| [Deployment](deployment.md) | Production deployment      |

## R&D (Research & Development)

| Topic                                 | Description                  |
| ------------------------------------- | ---------------------------- |
| [Django Parity](RnD/django-parity.md) | Feature comparison & roadmap |
| [AI Features R&D](RnD/ai-features.md) | AI architecture & providers  |
| [Architecture](RnD/architecture.md)   | Framework design decisions   |
| [Roadmap](RnD/roadmap.md)             | Future plans                 |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      P8s Application                        │
├─────────────────────────────────────────────────────────────┤
│  Frontend (5173)          │  Backend (8000)                 │
│  ├── React + Vite         │  ├── FastAPI                    │
│  ├── TypeScript           │  ├── SQLModel ORM               │
│  └── TanStack Query       │  ├── JWT Auth                   │
│                           │  ├── Admin Panel (/admin/)      │
│                           │  └── AI Integration (optional)  │
└───────────────────────────┴─────────────────────────────────┘
```

## Quick Start

```bash
# Install
pip install p8s

# Create project
p8s new project myapp
cd myapp

# Start development
p8s dev

# Open http://localhost:5173 (frontend)
# Open http://localhost:8000/admin (admin panel)
```

## License

MIT — steal the fire, responsibly 🔥
