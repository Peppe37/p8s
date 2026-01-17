# How to Create Custom CLI Commands

P8s creates a powerful CLI based on `Typer` but allows you to add custom commands in a Django-style way.

## Step 1: Create Commands Directory

Inside your app, create a `commands` directory:

```bash
mkdir -p backend/blog/commands
touch backend/blog/commands/__init__.py
```

## Step 2: Create Command File

Create a file for your command (e.g., `publish_posts.py`):

```python
# backend/blog/commands/publish_posts.py
from p8s.cli.commands import Command

class PublishPostsCommand(Command):
    name = "publish-posts"
    help = "Publish all draft posts marked for today"

    def add_arguments(self, parser):
        # Add standard argparse arguments
        parser.add_argument("--dry-run", action="store_true", help="Simulate publishing")

    async def handle(self, **options):
        dry_run = options["dry_run"]

        # Your logic here
        if dry_run:
            self.stdout.warning("Dry run mode - no changes made")
        else:
            self.stdout.success("Published 5 posts!")
```

## Step 3: Run Command

Your command is automatically discovered and registered. Run it via `p8s`:

```bash
p8s publish-posts --dry-run
```

## Advanced Usage

You can access the database, settings, and other P8s features within your command:

```python
from p8s.db.session import SessionManager
from backend.blog.models import Post

async def handle(self, **options):
    async with SessionManager() as session:
        posts = await session.exec(...)
        # ...
```
