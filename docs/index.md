# P8s Framework Documentation

Welcome to the **P8s (Prometheus)** documentation. This guide will help you build AI-native, full-stack applications.

## Table of Contents

- [Getting Started](getting-started.md)
- [CLI Reference](cli.md)
- [Models & Database](models.md)
- [Authentication](authentication.md)
- [Admin Panel](admin.md)
- [AI Features](ai.md)
- [Configuration](configuration.md)
- [Deployment](deployment.md)

---

## Quick Links

| Topic                                 | Description                      |
| ------------------------------------- | -------------------------------- |
| [Getting Started](getting-started.md) | Create your first P8s project    |
| [CLI Reference](cli.md)               | All available commands           |
| [Admin Panel](admin.md)               | Django-style admin interface     |
| [AI Features](ai.md)                  | AIField, VectorField, embeddings |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      P8s Application                        │
├─────────────────────────────────────────────────────────────┤
│  Frontend (5173)          │  Backend (8000)                 │
│  ├── React + Vite         │  ├── FastAPI                    │
│  ├── TypeScript           │  ├── SQLModel ORM               │
│  └── TailwindCSS          │  ├── JWT Auth                   │
│                           │  ├── Admin Panel (/admin/)      │
│                           │  └── AI Integration             │
└───────────────────────────┴─────────────────────────────────┘
```

## License

MIT — steal the fire, responsibly 🔥
