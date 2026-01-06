# CLI Reference

P8s provides a powerful command-line interface for managing your projects.

## Installation

The CLI is installed automatically with the P8s package:

```bash
pip install -e ".[all]"
```

## Commands Overview

| Command                  | Description                       |
| ------------------------ | --------------------------------- |
| `p8s new project <name>` | Create a new P8s project          |
| `p8s new app <name>`     | Create a new app within a project |
| `p8s dev`                | Start development server          |
| `p8s migrate`            | Run database migrations           |
| `p8s makemigrations`     | Generate new migrations           |
| `p8s createsuperuser`    | Create admin user                 |
| `p8s shell`              | Interactive Python shell          |
| `p8s version`            | Show P8s version                  |

---

## `p8s new project`

Create a new P8s project with the standard directory structure.

```bash
p8s new project myapp
```

**Options:**

| Option           | Description         |
| ---------------- | ------------------- |
| `--no-frontend`  | Skip frontend setup |
| `--db-url <url>` | Custom database URL |

**Example:**

```bash
p8s new project myapp --no-frontend --db-url "postgresql+asyncpg://user:pass@localhost/mydb"
```

---

## `p8s new app`

Create a new app within your project.

```bash
p8s new app blog
```

Creates:
```
backend/apps/blog/
├── __init__.py
├── models.py
└── router.py
```

---

## `p8s dev`

Start the development server with hot-reload.

```bash
p8s dev
```

**Options:**

| Option                     | Default      | Description             |
| -------------------------- | ------------ | ----------------------- |
| `--host`                   | `0.0.0.0`    | Host to bind            |
| `--port`                   | `8000`       | Port for backend        |
| `--frontend/--no-frontend` | `--frontend` | Enable/disable frontend |

**Examples:**

```bash
# Start on port 3000
p8s dev --port 3000

# Backend only
p8s dev --no-frontend

# Custom host
p8s dev --host 127.0.0.1 --port 8080
```

**Output with colored tags:**

```
[backend] INFO: Uvicorn running on http://0.0.0.0:8000
[backend] INFO: Application startup complete.
[frontend] VITE v4.5.14 ready in 456ms
[frontend] ➜ Local: http://localhost:5173/
```

---

## `p8s migrate`

Apply database migrations.

```bash
p8s migrate
```

This creates tables based on your SQLModel definitions.

---

## `p8s makemigrations`

Generate new migration files (if using Alembic).

```bash
p8s makemigrations -m "Add products table"
```

---

## `p8s createsuperuser`

Create an admin user for the admin panel.

```bash
p8s createsuperuser
```

Interactive prompts:
```
Email: admin@example.com
Password: ****
Repeat for confirmation: ****

✓ Superuser created successfully!
  ID: abc123...
  Email: admin@example.com
  Role: UserRole.SUPERUSER
```

**Options:**

| Option              | Description       |
| ------------------- | ----------------- |
| `--email <email>`   | Pre-fill email    |
| `--username <name>` | Optional username |

---

## `p8s shell`

Open an interactive Python shell with your app context loaded.

```bash
p8s shell
```

```python
>>> from backend.models import Product
>>> products = await Product.all()
>>> len(products)
42
```

---

## `p8s version`

Show the installed P8s version.

```bash
p8s version
# P8s version 0.1.0
```

---

## Environment Variables

The CLI respects the following environment variables:

| Variable              | Description                 |
| --------------------- | --------------------------- |
| `P8S_SETTINGS_MODULE` | Custom settings module path |
| `DATABASE_URL`        | Database connection string  |
| `SECRET_KEY`          | JWT secret key              |

---

## Exit Codes

| Code | Meaning                               |
| ---- | ------------------------------------- |
| `0`  | Success                               |
| `1`  | General error                         |
| `2`  | Command not found / Invalid arguments |
