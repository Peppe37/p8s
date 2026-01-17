# Models & Database

P8s uses **SQLModel** (SQLAlchemy + Pydantic) for database models.

## Base Model

All models should extend `p8s.Model`:

```python
from p8s import Model
from sqlmodel import Field

class Product(Model, table=True):
    name: str = Field(index=True)
    description: str = ""
    price: float = 0.0
    is_active: bool = True
```

### Inherited Features

The base `Model` class provides:

| Field        | Type       | Description                |
| ------------ | ---------- | -------------------------- |
| `id`         | `UUID`     | Auto-generated primary key |
| `created_at` | `datetime` | Auto-set on creation       |
| `updated_at` | `datetime` | Auto-updated on save       |
| `deleted_at` | `datetime` | Soft delete timestamp      |

## Database Configuration

Configure in `.env`:

```env
# SQLite (default)
DATABASE_URL=sqlite+aiosqlite:///p8s.db

# PostgreSQL
DATABASE_URL=postgresql+asyncpg://user:password@localhost/dbname

# PostgreSQL with pgvector (for AI features)
DATABASE_URL=postgresql+asyncpg://user:password@localhost/dbname?server_settings=vector.enable=on
```

## Relationships

### One-to-Many

```python
from uuid import UUID

class Author(Model, table=True):
    name: str

class Book(Model, table=True):
    title: str
    author_id: UUID = Field(foreign_key="author.id")
```

### Many-to-Many

```python
from sqlmodel import Relationship

class BookTag(Model, table=True):
    book_id: UUID = Field(foreign_key="book.id", primary_key=True)
    tag_id: UUID = Field(foreign_key="tag.id", primary_key=True)

class Tag(Model, table=True):
    name: str
    books: list["Book"] = Relationship(back_populates="tags", link_model=BookTag)

class Book(Model, table=True):
    title: str
    tags: list[Tag] = Relationship(back_populates="books", link_model=BookTag)
```

## CRUD Operations

### Create

```python
from p8s.db.session import get_session

async with get_session() as session:
    product = Product(name="Widget", price=9.99)
    session.add(product)
    await session.commit()
```

### Read

```python
from sqlmodel import select

async with get_session() as session:
    # Get by ID
    result = await session.get(Product, product_id)

    # Query all
    result = await session.execute(select(Product))
    products = result.scalars().all()

    # Filter
    result = await session.execute(
        select(Product).where(Product.is_active == True)
    )
```

### Update

```python
async with get_session() as session:
    product = await session.get(Product, product_id)
    product.price = 19.99
    session.add(product)
    await session.commit()
```

### Delete

```python
# Soft delete (recommended)
product.soft_delete()
session.add(product)
await session.commit()

# Hard delete
await session.delete(product)
await session.commit()
```

## Soft Delete

All models support soft delete by default:

```python
# Soft delete
product.soft_delete()

# Restore
product.restore()

# Query includes soft-deleted items
select(Product).where(Product.deleted_at.is_(None))
```

## Migrations

### Create tables

```bash
p8s migrate
```

### With Alembic (advanced)

```bash
# Generate migration
p8s makemigrations -m "Add products table"

# Apply migrations
p8s migrate
```

## Best Practices

1. **Always use UUIDs** (handled by base Model)
2. **Use soft deletes** for audit trails
3. **Index frequently queried fields**
4. **Use `table=True`** for database-backed models

## Standalone Scripts & Seeding

For scripts that run outside the API context (e.g., seeding data, cron jobs, data analysis), use the `setup_context` utility. This ensures the database and settings are correctly initialized.

```python
import asyncio
from p8s.core.context import setup_context
from p8s.db.session import SessionManager
from backend.models import Product

async def main():
    async with setup_context():
        async with SessionManager() as session:
            # Full ORM access
            product = Product(name="Script created", price=10.0)
            session.add(product)
            await session.commit()

if __name__ == "__main__":
    asyncio.run(main())
```

Use `p8s seed` to execute these scripts easily.
