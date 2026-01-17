# How to Create a New App

P8s uses a modular structure similar to Django. An "App" is a self-contained module with its own models, views, and logic.

## Step 1: Create App Directory

Create a directory for your app within your project (e.g., inside `backend/` or at the root):

```bash
mkdir -p backend/blog
touch backend/blog/__init__.py
```

## Step 2: Define Models

Create a `models.py` file to define your data structure:

```python
# backend/blog/models.py
from datetime import datetime
from sqlmodel import Field, SQLModel
from p8s.admin import register_model

@register_model
class Post(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    content: str
    published: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Admin:
        list_display = ["title", "published", "created_at"]
        search_fields = ["title", "content"]
        list_filter = ["published"]
```

The `@register_model` decorator automatically adds it to the admin panel.

## Step 3: Register App

Add your new app to `INSTALLED_APPS` in `backend/settings.py`:

```python
# backend/settings.py
INSTALLED_APPS = [
    # ... existing apps ...
    "backend.blog",
]
```

## Step 4: Create Migrations

Generate a migration file for your new models:

```bash
p8s makemigrations --message "Add blog app"
```

## Step 5: Apply Migrations

Apply the changes to the database:

```bash
p8s migrate
```

Your new `Post` model is now live and accessible in the admin panel!
