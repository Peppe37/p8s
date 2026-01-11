# Migrations

P8s uses Alembic for database migrations with **automatic model change detection**.

## Overview

| Command                       | Description                      |
| ----------------------------- | -------------------------------- |
| `p8s init-migrations`         | Initialize migrations            |
| `p8s makemigrations -m "msg"` | Create migration (auto-detected) |
| `p8s migrate`                 | Apply migrations                 |
| `p8s show-migrations`         | View history                     |

## Getting Started

### Initialize

```bash
p8s init-migrations
```

Creates:
```
migrations/
├── env.py
├── script.py.mako
└── versions/
alembic.ini
```

### Create Migration

```bash
p8s makemigrations -m "Create products table"
```

P8s automatically:
1. Imports models from all `installed_apps`
2. Compares models to current database schema
3. Generates migration with appropriate operations

### Apply

```bash
p8s migrate
```

---

## How Auto-Detection Works

The `env.py` template auto-discovers models:

```python
# Auto-discover models from installed apps
from p8s.core.settings import get_settings
import importlib

settings = get_settings()
for app_name in settings.installed_apps:
    importlib.import_module(f"{app_name}.models")

target_metadata = SQLModel.metadata
```

When you run `makemigrations`, Alembic:
1. Loads all model definitions into `SQLModel.metadata`
2. Inspects current database schema
3. Generates operations: `create_table`, `add_column`, `drop_column`, etc.

---

## Example Workflow

### 1. Define Model

```python
# backend/apps/products/models.py
from p8s import Model
from sqlmodel import Field

class Product(Model, table=True):
    name: str = Field(max_length=255)
    price: float = Field(ge=0)
```

### 2. Register App

```python
# backend/settings.py
installed_apps = ["backend.apps.products"]
```

### 3. Create Migration

```bash
p8s makemigrations -m "Create products table"
```

Generated migration:
```python
def upgrade():
    op.create_table('product',
        sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
```

### 4. Apply

```bash
p8s migrate
```

---

## Adding Fields

```python
# Add new field
class Product(Model, table=True):
    name: str = Field(max_length=255)
    price: float = Field(ge=0)
    description: str | None = None  # New!
```

```bash
p8s makemigrations -m "Add product description"
```

Generates:
```python
def upgrade():
    op.add_column('product', 
        sa.Column('description', sa.String(), nullable=True))
```

---

## Migration Commands

### Target Specific Revision

```bash
p8s migrate -r abc123
```

### View History

```bash
p8s show-migrations

┌──────────────┬──────────────────────┬──────────────┐
│ Revision     │ Message              │ Parent       │
├──────────────┼──────────────────────┼──────────────┤
│ abc123def456 │ Add product desc     │ 123abc456def │
│ 123abc456def │ Create products      │ None         │
└──────────────┴──────────────────────┴──────────────┘
```

---

## Manual Migrations

Disable auto-detection:

```bash
p8s makemigrations -m "Custom migration" --no-auto
```

Then edit the generated file manually.

---

## Database Support

P8s converts async database URLs for Alembic:

| Your URL                           | Alembic Uses                |
| ---------------------------------- | --------------------------- |
| `sqlite+aiosqlite:///./db.sqlite3` | `sqlite:///./db.sqlite3`    |
| `postgresql+asyncpg://...`         | `postgresql+psycopg2://...` |

---

## Best Practices

1. **Always version control migrations** - Commit to git
2. **Run in staging first** - Test migrations before production
3. **Backup before migrate** - Especially for data migrations
4. **Keep migrations small** - One logical change per migration
5. **Review generated code** - Auto-detection isn't perfect
