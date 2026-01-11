# CLI Reference

P8s provides a powerful command-line interface for managing your projects.

## Installation

The CLI is installed automatically with the P8s package:

```bash
pip install -e ".[all]"
```

## Commands Overview

| Command                  | Description                             |
| ------------------------ | --------------------------------------- |
| `p8s new project <name>` | Create a new P8s project                |
| `p8s new app <name>`     | Create a new app within a project       |
| `p8s dev`                | Start development server                |
| `p8s migrate`            | Run database migrations                 |
| `p8s makemigrations`     | Generate new migrations (auto-detected) |
| `p8s init-migrations`    | Initialize migrations directory         |
| `p8s show-migrations`    | Show migration history                  |
| `p8s createsuperuser`    | Create admin user                       |
| `p8s shell`              | Interactive Python shell                |
| `p8s check`              | Run system checks                       |
| `p8s dbshell`            | Open database shell                     |
| `p8s sendtestemail`      | Test email configuration                |
| `p8s dumpdata`           | Export data to fixture                  |
| `p8s loaddata`           | Import data from fixture                |
| `p8s collectstatic`      | Collect static files                    |
| `p8s types`              | Generate TypeScript types               |
| `p8s version`            | Show P8s version                        |

---

## Project Commands

### `p8s new project`

Create a new P8s project with the standard directory structure.

```bash
p8s new project myapp
```

**Options:**

| Option   | Description      |
| -------- | ---------------- |
| `--path` | Destination path |

---

### `p8s new app`

Create a new app within your project.

```bash
p8s new app blog
```

Creates:
```
backend/apps/blog/
├── __init__.py
├── models.py
├── router.py
└── schemas.py
```

---

## Development

### `p8s dev`

Start the development server with hot-reload for both backend and frontend.

```bash
p8s dev
```

**Options:**

| Option                     | Default      | Description             |
| -------------------------- | ------------ | ----------------------- |
| `--host`                   | `0.0.0.0`    | Host to bind            |
| `--port`                   | `8000`       | Port for backend        |
| `--frontend/--no-frontend` | `--frontend` | Enable/disable frontend |

**Output:**
```
[backend] INFO: Uvicorn running on http://0.0.0.0:8000
[frontend] VITE ready at http://localhost:5173/
```

---

## Database & Migrations

### `p8s init-migrations`

Initialize the migrations directory with Alembic configuration.

```bash
p8s init-migrations
```

### `p8s makemigrations`

Generate a new migration with **automatic model change detection**.

```bash
p8s makemigrations -m "Add product description"
```

**Options:**

| Option             | Description                         |
| ------------------ | ----------------------------------- |
| `-m, --message`    | Migration description (required)    |
| `--auto/--no-auto` | Auto-detect changes (default: auto) |

P8s uses Alembic under the hood and automatically:
- Imports models from all `installed_apps`
- Compares current models to database schema
- Generates migration with `op.add_column()`, `op.create_table()`, etc.

### `p8s migrate`

Apply database migrations.

```bash
p8s migrate
p8s migrate -r abc123  # Migrate to specific revision
```

### `p8s show-migrations`

Display migration history.

```bash
p8s show-migrations
```

### `p8s dbshell`

Open the database shell based on `DATABASE_URL`.

```bash
p8s dbshell
```

Opens `sqlite3`, `psql`, or `mysql` depending on your database.

---

## Data Management

### `p8s dumpdata`

Export data to a fixture file.

```bash
p8s dumpdata -o fixtures/backup.json
p8s dumpdata -m Product -m Category -o products.json
p8s dumpdata --format yaml -o data.yaml
```

**Options:**

| Option         | Description               |
| -------------- | ------------------------- |
| `-o, --output` | Output file path          |
| `-m, --model`  | Specific models to dump   |
| `-f, --format` | Output format (json/yaml) |

### `p8s loaddata`

Import data from a fixture file.

```bash
p8s loaddata fixtures/initial_data.json
p8s loaddata data.yaml
```

---

## Users & Auth

### `p8s createsuperuser`

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
```

**Options:**

| Option       | Description       |
| ------------ | ----------------- |
| `--email`    | Pre-fill email    |
| `--username` | Optional username |

---

## System Commands

### `p8s check`

Run system checks to validate configuration.

```bash
p8s check
p8s check --deploy  # Additional production checks
```

**Output:**
```
Running system checks...

  Checking settings... OK
  Checking database... OK
  Checking installed apps... OK (3 apps)
  Checking admin models... OK (5 models)
  Checking migrations... OK

✓ All checks passed!
```

With `--deploy`:
- Verifies DEBUG is False
- Checks SECRET_KEY is not default
- Warns about SQLite in production

### `p8s sendtestemail`

Test email configuration by sending a test email.

```bash
p8s sendtestemail admin@example.com
```

### `p8s collectstatic`

Collect static files from apps into STATIC_ROOT.

```bash
p8s collectstatic
p8s collectstatic --clear  # Clear destination first
p8s collectstatic --dry-run  # Preview without copying
```

### `p8s shell`

Open an interactive Python shell with app context.

```bash
p8s shell
```

### `p8s version`

Show the installed P8s version.

```bash
p8s version
# P8s version 0.1.0
```

---

## Custom Commands

P8s supports Django-style custom management commands.

### Creating a Command

Create a command file in your app:

```
backend/apps/myapp/management/commands/send_reports.py
```

```python
"""Send weekly reports."""

async def command():
    """Send reports to all users."""
    print("Sending reports...")
    # Your logic here
```

### Running Commands

```bash
p8s run send_reports
p8s list-commands  # Show all custom commands
```

---

## Environment Variables

| Variable              | Description                 |
| --------------------- | --------------------------- |
| `P8S_SETTINGS_MODULE` | Custom settings module path |
| `P8S_DB_URL`          | Database connection string  |
| `P8S_SECRET_KEY`      | JWT secret key              |
| `P8S_DEBUG`           | Enable debug mode           |

---

## Exit Codes

| Code | Meaning           |
| ---- | ----------------- |
| `0`  | Success           |
| `1`  | General error     |
| `2`  | Command not found |
