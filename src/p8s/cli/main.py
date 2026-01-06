"""
P8s CLI - The sacred fire command line interface.

Usage:
    p8s new project myapp
    p8s new app blog
    p8s dev
    p8s migrate
    p8s shell
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

app = typer.Typer(
    name="p8s",
    help="🔥 P8s CLI - Forge AI-native, full-stack applications",
    add_completion=True,
)

console = Console()


def print_banner():
    """Print the P8s banner."""
    banner = """
🔥 P8s (Prometheus)
━━━━━━━━━━━━━━━━━━━
Forge AI-native applications with the fire of the gods.
    """
    console.print(Panel(banner, border_style="red"))


# ============================================================================
# NEW command group
# ============================================================================

new_app = typer.Typer(help="Create new projects and apps")
app.add_typer(new_app, name="new")


@new_app.command("project")
def new_project(
    name: str = typer.Argument(..., help="Project name"),
    path: Optional[Path] = typer.Option(
        None, "--path", "-p", help="Destination path"
    ),
):
    """
    Create a new P8s project.

    Example:
        p8s new project myapp
        p8s new project myapp --path ./projects
    """
    print_banner()

    dest = (path or Path.cwd()) / name

    if dest.exists():
        console.print(f"[red]Error:[/red] Directory {dest} already exists")
        raise typer.Exit(1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Creating project structure...", total=None)

        # Create directories
        (dest / "backend" / "apps").mkdir(parents=True)
        (dest / "frontend" / "src" / "pages").mkdir(parents=True)
        (dest / "frontend" / "src" / "components").mkdir(parents=True)
        (dest / "frontend" / "src" / "types").mkdir(parents=True)
        (dest / "static").mkdir()
        (dest / "media").mkdir()
        (dest / "tests").mkdir()

        progress.update(task, description="Writing configuration files...")

        # Write main.py
        main_content = f'''"""
{name} - A P8s Application
"""

from p8s import P8sApp

app = P8sApp(title="{name}")


@app.get("/")
async def root():
    return {{"message": "Welcome to {name}! 🔥"}}


@app.get("/health")
async def health():
    return {{"status": "healthy"}}
'''
        (dest / "backend" / "main.py").write_text(main_content)

        # Write models.py
        models_content = '''"""
Database models for the application.
"""

from p8s import Model
from sqlmodel import Field


# Define your models here
# Example:
#
# class Product(Model, table=True):
#     name: str = Field(max_length=255)
#     price: float = Field(ge=0)
#     description: str | None = None
'''
        (dest / "backend" / "models.py").write_text(models_content)

        # Write settings.py
        settings_content = '''"""
Application settings.

Override using environment variables prefixed with P8S_
Example: P8S_DEBUG=true
"""

from p8s.core.settings import Settings

# Extend settings if needed
class AppSettings(Settings):
    pass
'''
        (dest / "backend" / "settings.py").write_text(settings_content)

        # Write pyproject.toml
        pyproject_content = f'''[project]
name = "{name}"
version = "0.1.0"
description = "A P8s application"
requires-python = ">=3.10"
dependencies = [
    "p8s",
]

[project.optional-dependencies]
dev = [
    "pytest",
    "pytest-asyncio",
]
'''
        (dest / "pyproject.toml").write_text(pyproject_content)

        # Write .env.example
        env_content = '''# P8s Configuration
P8S_DEBUG=true
P8S_SECRET_KEY=your-secret-key-change-in-production

# Database
P8S_DB_URL=sqlite+aiosqlite:///./db.sqlite3

# AI (optional)
# P8S_AI_OPENAI_API_KEY=sk-...
# P8S_AI_PROVIDER=openai
# P8S_AI_MODEL=gpt-4o-mini
'''
        (dest / ".env.example").write_text(env_content)
        (dest / ".env").write_text(env_content)

        # Write .gitignore
        gitignore_content = '''# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
.env

# Database
*.sqlite3
*.db

# IDE
.vscode/
.idea/

# Build
dist/
build/
*.egg-info/

# Frontend
node_modules/
frontend/dist/
'''
        (dest / ".gitignore").write_text(gitignore_content)

        progress.update(task, description="Setting up frontend...")

        # Write frontend package.json
        package_json = f'''{{
  "name": "{name}-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {{
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  }},
  "dependencies": {{
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@tanstack/react-query": "^5.0.0"
  }},
  "devDependencies": {{
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@vitejs/plugin-react": "^4.2.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0"
  }}
}}
'''
        (dest / "frontend" / "package.json").write_text(package_json)

        # Write vite.config.ts
        vite_config = '''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/admin': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
'''
        (dest / "frontend" / "vite.config.ts").write_text(vite_config)

        # Write index.html
        index_html = f'''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{name}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
'''
        (dest / "frontend" / "index.html").write_text(index_html)

        # Write main.tsx
        main_tsx = '''import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'
import './index.css'

const queryClient = new QueryClient()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>,
)
'''
        (dest / "frontend" / "src" / "main.tsx").write_text(main_tsx)

        # Write App.tsx
        app_tsx = f'''import {{ useQuery }} from '@tanstack/react-query'

function App() {{
  const {{ data, isLoading }} = useQuery({{
    queryKey: ['health'],
    queryFn: () => fetch('/api/health').then(res => res.json()),
  }})

  return (
    <div className="app">
      <header>
        <h1>🔥 {name}</h1>
        <p>A P8s Application</p>
      </header>
      <main>
        {{isLoading ? (
          <p>Loading...</p>
        ) : (
          <p>API Status: {{data?.status || 'unknown'}}</p>
        )}}
      </main>
    </div>
  )
}}

export default App
'''
        (dest / "frontend" / "src" / "App.tsx").write_text(app_tsx)

        # Write index.css
        index_css = ''':root {
  --primary: #f97316;
  --bg: #0f0f0f;
  --text: #fafafa;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', system-ui, sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
}

.app {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

header {
  text-align: center;
  margin-bottom: 3rem;
}

header h1 {
  font-size: 3rem;
  background: linear-gradient(135deg, var(--primary), #fbbf24);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 0.5rem;
}

header p {
  color: #888;
}

main {
  background: #1a1a1a;
  border-radius: 1rem;
  padding: 2rem;
  border: 1px solid #333;
}
'''
        (dest / "frontend" / "src" / "index.css").write_text(index_css)

        # Write tsconfig.json
        tsconfig = '''{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
'''
        (dest / "frontend" / "tsconfig.json").write_text(tsconfig)

        tsconfig_node = '''{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
'''
        (dest / "frontend" / "tsconfig.node.json").write_text(tsconfig_node)

        progress.update(task, description="Done!")

    console.print()
    console.print(f"[green]✓[/green] Project created at [bold]{dest}[/bold]")
    console.print()
    console.print("Next steps:")
    console.print(f"  cd {name}")
    console.print("  pip install -e .")
    console.print("  cd frontend && npm install && cd ..")
    console.print("  p8s dev")


@new_app.command("app")
def new_app_cmd(
    name: str = typer.Argument(..., help="App name"),
):
    """
    Create a new app within a project.

    Example:
        p8s new app blog
    """
    # Check we're in a P8s project
    if not Path("backend").exists():
        console.print("[red]Error:[/red] Not in a P8s project directory")
        raise typer.Exit(1)

    apps_dir = Path("backend") / "apps" / name

    if apps_dir.exists():
        console.print(f"[red]Error:[/red] App {name} already exists")
        raise typer.Exit(1)

    apps_dir.mkdir(parents=True)

    # Write __init__.py
    (apps_dir / "__init__.py").write_text(f'"""{name} app"""\n')

    # Write models.py
    models_content = f'''"""
{name} models.
"""

from p8s import Model
from sqlmodel import Field


# Define your models here
'''
    (apps_dir / "models.py").write_text(models_content)

    # Write router.py
    router_content = f'''"""
{name} API routes.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from p8s.db.session import get_session

router = APIRouter()


@router.get("/")
async def list_{name}():
    return []
'''
    (apps_dir / "router.py").write_text(router_content)

    # Write schemas.py
    schemas_content = f'''"""
{name} schemas.
"""

from pydantic import BaseModel


# Define your schemas here
'''
    (apps_dir / "schemas.py").write_text(schemas_content)

    console.print(f"[green]✓[/green] App [bold]{name}[/bold] created")
    console.print()
    console.print("Register it in your settings.py:")
    console.print(f'  installed_apps = ["backend.apps.{name}"]')


# ============================================================================
# DEV command
# ============================================================================

@app.command()
def dev(
    host: str = typer.Option("0.0.0.0", "--host", "-h"),
    port: int = typer.Option(8000, "--port", "-p"),
    frontend: bool = typer.Option(True, "--frontend/--no-frontend"),
):
    """
    Start the development server.

    Runs both backend (Uvicorn) and frontend (Vite) in parallel.

    Example:
        p8s dev
        p8s dev --port 3000
        p8s dev --no-frontend
    """
    import asyncio
    import signal

    print_banner()

    console.print(f"[bold]Starting development server...[/bold]")
    console.print(f"  Backend:  http://{host}:{port}")
    if frontend:
        console.print(f"  Frontend: http://localhost:5173")
    console.print()

    processes = []

    try:
        # Start backend
        backend_cmd = [
            sys.executable, "-m", "uvicorn",
            "backend.main:app",
            "--host", host,
            "--port", str(port),
            "--reload",
        ]

        backend_proc = subprocess.Popen(backend_cmd)
        processes.append(backend_proc)

        # Start frontend if enabled
        if frontend and Path("frontend").exists():
            frontend_cmd = ["npm", "run", "dev"]

            frontend_proc = subprocess.Popen(
                frontend_cmd,
                cwd="frontend",
            )
            processes.append(frontend_proc)

        # Wait for processes
        for proc in processes:
            proc.wait()

    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down...[/yellow]")
        for proc in processes:
            proc.terminate()
        for proc in processes:
            proc.wait()


# ============================================================================
# MIGRATE commands
# ============================================================================

@app.command()
def migrate(
    revision: str = typer.Option("head", "--revision", "-r", help="Target revision"),
):
    """
    Run database migrations.

    Example:
        p8s migrate
        p8s migrate -r abc123
    """
    from pathlib import Path

    migrations_dir = Path.cwd() / "migrations"

    if not migrations_dir.exists():
        console.print("[yellow]No migrations found. Run 'p8s init-migrations' first.[/yellow]")
        raise typer.Exit(1)

    console.print(f"[bold]Running migrations to {revision}...[/bold]")

    try:
        from p8s.db.migrations import run_migrations
        run_migrations(revision, migrations_dir)
        console.print("[green]✓[/green] Migrations applied successfully!")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def makemigrations(
    message: str = typer.Option(..., "--message", "-m", prompt="Migration message"),
    autogenerate: bool = typer.Option(True, "--auto/--no-auto"),
):
    """
    Create a new migration.

    Example:
        p8s makemigrations -m "Add product model"
    """
    from pathlib import Path

    migrations_dir = Path.cwd() / "migrations"

    if not migrations_dir.exists():
        console.print("[yellow]No migrations directory. Run 'p8s init-migrations' first.[/yellow]")
        raise typer.Exit(1)

    console.print(f"[bold]Creating migration: {message}[/bold]")

    try:
        from p8s.db.migrations import create_migration
        revision = create_migration(message, autogenerate, migrations_dir)
        console.print(f"[green]✓[/green] Created migration: {revision}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("init-migrations")
def init_migrations_cmd():
    """
    Initialize migrations directory.

    Example:
        p8s init-migrations
    """
    from pathlib import Path

    migrations_dir = Path.cwd() / "migrations"

    if migrations_dir.exists():
        console.print("[yellow]Migrations directory already exists.[/yellow]")
        raise typer.Exit(1)

    console.print("[bold]Initializing migrations...[/bold]")

    try:
        from p8s.db.migrations import init_migrations
        init_migrations(migrations_dir)
        console.print("[green]✓[/green] Migrations initialized!")
        console.print(f"  Directory: {migrations_dir}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("show-migrations")
def show_migrations_cmd():
    """
    Show migration history.

    Example:
        p8s show-migrations
    """
    from pathlib import Path

    migrations_dir = Path.cwd() / "migrations"

    if not migrations_dir.exists():
        console.print("[yellow]No migrations found.[/yellow]")
        raise typer.Exit(1)

    try:
        from p8s.db.migrations import show_migrations
        migrations = show_migrations(migrations_dir)

        if not migrations:
            console.print("[dim]No migrations yet.[/dim]")
            return

        table = Table(title="Migrations")
        table.add_column("Revision", style="cyan")
        table.add_column("Message")
        table.add_column("Parent")

        for m in migrations:
            table.add_row(
                m["revision"][:12],
                m["message"] or "",
                (m["down_revision"] or "")[:12],
            )

        console.print(table)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


# ============================================================================
# SHELL command
# ============================================================================

@app.command()
def shell():
    """
    Start an interactive Python shell with the app context.
    """
    import code

    console.print("[bold]P8s Interactive Shell[/bold]")
    console.print("Available: app, session, models")
    console.print()

    # TODO: Load app context
    local_vars = {
        "console": console,
    }

    code.interact(local=local_vars)


# ============================================================================
# TYPES command
# ============================================================================

@app.command()
def types(
    output: Path = typer.Option(
        Path("frontend/src/types"),
        "--output", "-o",
    ),
):
    """
    Generate TypeScript types from Python models.

    Example:
        p8s types
        p8s types -o ./types
    """
    console.print("[bold]Generating TypeScript types...[/bold]")

    # TODO: Implement type generation
    console.print("[yellow]Type generation coming soon![/yellow]")


# ============================================================================
# VERSION command
# ============================================================================

@app.command()
def version():
    """Show P8s version."""
    from p8s import __version__

    console.print(f"P8s version [bold]{__version__}[/bold]")


# ============================================================================
# Main entry
# ============================================================================

def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
