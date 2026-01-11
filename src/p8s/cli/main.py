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


def ensure_settings_module():
    """
    Ensure P8S_SETTINGS_MODULE is set for project settings discovery.
    
    This enables Django-style settings loading where projects can define
    their own AppSettings class that extends Settings.
    """
    import os
    
    if "P8S_SETTINGS_MODULE" not in os.environ:
        settings_file = Path.cwd() / "backend" / "settings.py"
        if settings_file.exists():
            os.environ["P8S_SETTINGS_MODULE"] = "backend.settings"


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

[tool.setuptools.packages.find]
include = ["backend*"]
'''
        (dest / "pyproject.toml").write_text(pyproject_content)

        # Write .env.example
        env_content = '''# P8s Configuration
P8S_DEBUG=true
P8S_SETTINGS_MODULE=backend.settings
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
    "@types/node": "^20.0.0",
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
        target: `http://localhost:${process.env.P8S_DEV_PORT || '8000'}`,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      '/admin': {
        target: `http://localhost:${process.env.P8S_DEV_PORT || '8000'}`,
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
    import os
    import threading
    import select

    print_banner()

    console.print(f"[bold]Starting development server...[/bold]")
    console.print(f"  Backend:  http://{host}:{port}")
    if frontend:
        console.print(f"  Frontend: http://localhost:5173")
    console.print()

    processes = []
    
    def stream_output(proc, prefix: str, color: str):
        """Stream process output with colored prefix."""
        try:
            for line in iter(proc.stdout.readline, b''):
                if line:
                    text = line.decode('utf-8', errors='replace').rstrip()
                    console.print(f"[{color}][{prefix}][/{color}] {text}")
        except Exception:
            pass
    
    def stream_stderr(proc, prefix: str, color: str):
        """Stream process stderr with colored prefix."""
        try:
            for line in iter(proc.stderr.readline, b''):
                if line:
                    text = line.decode('utf-8', errors='replace').rstrip()
                    console.print(f"[{color}][{prefix}][/{color}] {text}")
        except Exception:
            pass

    try:
        # Start backend
        import p8s
        framework_dir = Path(p8s.__file__).parent
        
        # Set up environment with settings module discovery
        env = os.environ.copy()
        
        # Auto-discover settings module if not already set
        if "P8S_SETTINGS_MODULE" not in env:
            settings_file = Path.cwd() / "backend" / "settings.py"
            if settings_file.exists():
                env["P8S_SETTINGS_MODULE"] = "backend.settings"
        
        backend_cmd = [
            sys.executable, "-m", "uvicorn",
            "backend.main:app",
            "--host", host,
            "--port", str(port),
            "--reload",
            "--reload-dir", str(Path.cwd()),
            "--reload-dir", str(framework_dir),
        ]

        backend_proc = subprocess.Popen(
            backend_cmd, 
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        processes.append(backend_proc)
        
        # Start backend output streaming thread
        backend_thread = threading.Thread(
            target=stream_output, 
            args=(backend_proc, "backend", "cyan"),
            daemon=True
        )
        backend_thread.start()

        # Start frontend if enabled
        if frontend and Path("frontend").exists():
            env["P8S_DEV_PORT"] = str(port)

            frontend_cmd = ["npm", "run", "dev"]

            frontend_proc = subprocess.Popen(
                frontend_cmd,
                cwd="frontend",
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            processes.append(frontend_proc)
            
            # Start frontend output streaming thread
            frontend_thread = threading.Thread(
                target=stream_output,
                args=(frontend_proc, "frontend", "magenta"),
                daemon=True
            )
            frontend_thread.start()

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
# COLLECTSTATIC command
# ============================================================================

@app.command()
def collectstatic(
    clear: bool = typer.Option(False, "--clear", "-c", help="Clear destination before collecting"),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Show what would be collected"),
):
    """
    Collect static files from apps into STATIC_ROOT.
    
    Example:
        p8s collectstatic
        p8s collectstatic --clear
    """
    ensure_settings_module()
    
    console.print("[bold]Collecting static files...[/bold]")
    
    try:
        from p8s.core.settings import get_settings
        from p8s.staticfiles import StaticFilesConfig, collectstatic as do_collect
        
        settings = get_settings()
        
        # Build config from settings
        config = StaticFilesConfig(
            static_url=getattr(settings, "static_url", "/static/"),
            static_root=getattr(settings, "static_root", "staticfiles"),
            staticfiles_dirs=getattr(settings, "staticfiles_dirs", []),
            media_url=getattr(settings, "media_url", "/media/"),
            media_root=getattr(settings, "media_root", "media"),
        )
        
        if dry_run:
            console.print(f"[dim]Would collect to: {config.static_root}[/dim]")
            for src_dir in config.staticfiles_dirs:
                if Path(src_dir).exists():
                    count = sum(1 for _ in Path(src_dir).rglob("*") if _.is_file())
                    console.print(f"  {src_dir}: {count} files")
            return
        
        stats = do_collect(config, clear=clear)
        
        console.print(f"[green]✓[/green] Collected to {config.static_root}")
        console.print(f"  Copied: {stats['copied']} files")
        console.print(f"  Skipped: {stats['skipped']} files")
        
        if stats["errors"]:
            console.print(f"[yellow]Errors: {len(stats['errors'])}[/yellow]")
            for err in stats["errors"][:5]:
                console.print(f"  - {err}")
                
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


# ============================================================================
# VERSION command
# ============================================================================

@app.command()
def version():
    """Show P8s version."""
    from p8s import __version__

    console.print(f"P8s version [bold]{__version__}[/bold]")


# ============================================================================
# DBSHELL command
# ============================================================================

@app.command()
def dbshell():
    """
    Open the database shell.
    
    Opens sqlite3, psql, or mysql based on DATABASE_URL.
    
    Example:
        p8s dbshell
    """
    import os
    import shutil
    
    ensure_settings_module()
    
    from p8s.core.settings import get_settings
    settings = get_settings()
    
    db_url = settings.database.url
    
    # Parse database URL to determine type
    if db_url.startswith("sqlite"):
        # Extract path from sqlite URL
        # sqlite+aiosqlite:///./db.sqlite3 -> ./db.sqlite3
        path = db_url.split("///")[-1]
        
        if not shutil.which("sqlite3"):
            console.print("[red]Error:[/red] sqlite3 not found in PATH")
            raise typer.Exit(1)
        
        console.print(f"[bold]Opening SQLite database: {path}[/bold]")
        os.execvp("sqlite3", ["sqlite3", path])
        
    elif db_url.startswith("postgresql") or db_url.startswith("postgres"):
        # postgresql+asyncpg://user:pass@host:port/dbname
        if not shutil.which("psql"):
            console.print("[red]Error:[/red] psql not found in PATH")
            raise typer.Exit(1)
        
        # Convert async URL to regular for psql
        psql_url = db_url.replace("+asyncpg", "").replace("+psycopg2", "")
        console.print("[bold]Opening PostgreSQL database...[/bold]")
        os.execvp("psql", ["psql", psql_url])
        
    elif db_url.startswith("mysql"):
        if not shutil.which("mysql"):
            console.print("[red]Error:[/red] mysql client not found in PATH")
            raise typer.Exit(1)
        
        # Parse mysql URL for connection params
        # mysql+aiomysql://user:pass@host:port/dbname
        from urllib.parse import urlparse
        parsed = urlparse(db_url.replace("+aiomysql", "").replace("+pymysql", ""))
        
        args = ["mysql"]
        if parsed.hostname:
            args.extend(["-h", parsed.hostname])
        if parsed.port:
            args.extend(["-P", str(parsed.port)])
        if parsed.username:
            args.extend(["-u", parsed.username])
        if parsed.password:
            args.append(f"-p{parsed.password}")
        if parsed.path:
            args.append(parsed.path.lstrip("/"))
        
        console.print("[bold]Opening MySQL database...[/bold]")
        os.execvp("mysql", args)
    else:
        console.print(f"[red]Error:[/red] Unsupported database type in: {db_url}")
        raise typer.Exit(1)


# ============================================================================
# CHECK command
# ============================================================================

@app.command()
def check(
    deploy: bool = typer.Option(False, "--deploy", help="Run deployment checks"),
):
    """
    Run system checks.
    
    Validates settings, models, and configuration.
    
    Example:
        p8s check
        p8s check --deploy
    """
    ensure_settings_module()
    
    errors = []
    warnings = []
    
    console.print("[bold]Running system checks...[/bold]")
    console.print()
    
    # Check 1: Settings
    console.print("  Checking settings...", end=" ")
    try:
        from p8s.core.settings import get_settings
        settings = get_settings()
        console.print("[green]OK[/green]")
    except Exception as e:
        errors.append(f"Settings error: {e}")
        console.print("[red]FAIL[/red]")
    
    # Check 2: Database connectivity
    console.print("  Checking database...", end=" ")
    try:
        import asyncio
        from p8s.db.session import init_db, close_db
        
        async def _check_db():
            await init_db(settings.database)
            await close_db()
        
        asyncio.run(_check_db())
        console.print("[green]OK[/green]")
    except Exception as e:
        errors.append(f"Database error: {e}")
        console.print("[red]FAIL[/red]")
    
    # Check 3: Installed apps
    console.print("  Checking installed apps...", end=" ")
    try:
        import importlib
        for app_name in settings.installed_apps:
            importlib.import_module(app_name)
        console.print(f"[green]OK[/green] ({len(settings.installed_apps)} apps)")
    except ImportError as e:
        errors.append(f"App import error: {e}")
        console.print("[red]FAIL[/red]")
    
    # Check 4: Admin models
    console.print("  Checking admin models...", end=" ")
    try:
        from p8s.admin.registry import get_registered_models
        models = get_registered_models()
        console.print(f"[green]OK[/green] ({len(models)} models)")
    except Exception as e:
        warnings.append(f"Admin registry: {e}")
        console.print("[yellow]WARN[/yellow]")
    
    # Check 5: Migrations
    console.print("  Checking migrations...", end=" ")
    if Path("migrations").exists():
        console.print("[green]OK[/green]")
    else:
        warnings.append("No migrations directory found")
        console.print("[yellow]WARN[/yellow]")
    
    # Deployment checks
    if deploy:
        console.print()
        console.print("[bold]Deployment checks:[/bold]")
        
        # Debug mode
        console.print("  DEBUG mode...", end=" ")
        if settings.debug:
            errors.append("DEBUG is True - should be False in production")
            console.print("[red]FAIL[/red]")
        else:
            console.print("[green]OK[/green]")
        
        # Secret key
        console.print("  SECRET_KEY...", end=" ")
        if "change" in settings.secret_key.lower() or "default" in settings.secret_key.lower():
            errors.append("SECRET_KEY appears to be a default value")
            console.print("[red]FAIL[/red]")
        else:
            console.print("[green]OK[/green]")
        
        # Database URL
        console.print("  Database URL...", end=" ")
        if "sqlite" in settings.database.url:
            warnings.append("SQLite database - consider PostgreSQL for production")
            console.print("[yellow]WARN[/yellow]")
        else:
            console.print("[green]OK[/green]")
    
    # Summary
    console.print()
    if errors:
        console.print(f"[red]✗ {len(errors)} error(s) found:[/red]")
        for err in errors:
            console.print(f"  - {err}")
    
    if warnings:
        console.print(f"[yellow]! {len(warnings)} warning(s):[/yellow]")
        for warn in warnings:
            console.print(f"  - {warn}")
    
    if not errors and not warnings:
        console.print("[green]✓ All checks passed![/green]")
    elif not errors:
        console.print("[green]✓ No critical issues found[/green]")
    else:
        raise typer.Exit(1)


# ============================================================================
# SENDTESTEMAIL command
# ============================================================================

@app.command()
def sendtestemail(
    email: str = typer.Argument(..., help="Email address to send test to"),
):
    """
    Send a test email.
    
    Verifies email configuration is working.
    
    Example:
        p8s sendtestemail admin@example.com
    """
    import asyncio
    
    ensure_settings_module()
    
    console.print(f"[bold]Sending test email to {email}...[/bold]")
    
    try:
        from p8s.email import EmailMessage, get_email_backend
        
        message = EmailMessage(
            subject="P8s Test Email",
            body="""This is a test email from P8s.

If you received this email, your email configuration is working correctly.

Configuration details:
- Backend: {backend}
- Timestamp: {timestamp}

🔥 P8s Framework
            """.format(
                backend=type(get_email_backend()).__name__,
                timestamp=__import__("datetime").datetime.now().isoformat(),
            ),
            from_email="noreply@example.com",
            to=[email],
        )
        
        async def _send():
            result = await message.send()
            return result
        
        sent = asyncio.run(_send())
        
        if sent:
            console.print(f"[green]✓[/green] Test email sent successfully!")
        else:
            console.print(f"[yellow]![/yellow] Email queued (check backend logs)")
            
    except ImportError:
        console.print("[yellow]Note:[/yellow] Using console backend (email printed to stdout)")
        
        from p8s.email import EmailMessage
        message = EmailMessage(
            subject="P8s Test Email",
            body="This is a test email from P8s.\n\nIf you see this, email is configured correctly!",
            from_email="noreply@example.com",
            to=[email],
        )
        message.send()
        console.print("[green]✓[/green] Test email printed to console")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


# ============================================================================
# CREATESUPERUSER command
# ============================================================================

@app.command()
def createsuperuser(
    email: str = typer.Option(..., prompt=True),
    password: str = typer.Option(..., prompt=True, hide_input=True, confirmation_prompt=True),
    username: str = typer.Option(None, "--username", "-u"),
):
    """
    Create a superuser with admin privileges.
    
    Example:
        p8s createsuperuser
        p8s createsuperuser --email admin@example.com --username admin
    """
    import asyncio
    
    # Ensure settings module is loaded from project
    ensure_settings_module()
    
    from p8s.core.settings import get_settings
    from p8s.db.session import init_db, close_db, SessionManager
    from p8s.auth.models import User, UserRole
    from p8s.auth.security import get_password_hash
    from sqlmodel import select

    async def _create():
        settings = get_settings()
        await init_db(settings.database)

        try:
            async with SessionManager() as session:
                # Check if user exists
                query = select(User).where(User.email == email)
                result = await session.execute(query)
                existing = result.scalar_one_or_none()

                if existing:
                    console.print(f"[red]Error:[/red] User with email {email} already exists")
                    raise typer.Exit(1)

                # Create user
                user = User(
                    email=email,
                    password_hash=get_password_hash(password),
                    username=username,
                    role=UserRole.SUPERUSER,
                    is_active=True,
                    is_verified=True,
                )

                session.add(user)
                await session.commit()
                await session.refresh(user)

                console.print(f"[green]✓[/green] Superuser created created successfully!")
                console.print(f"  ID: {user.id}")
                console.print(f"  Email: {user.email}")
                console.print(f"  Role: {user.role}")
        finally:
            await close_db()

    asyncio.run(_create())

# ============================================================================
# FIXTURES - Data loading and dumping
# ============================================================================

@app.command("loaddata")
def loaddata(
    fixture_file: Path = typer.Argument(..., help="Path to fixture file (JSON/YAML)"),
):
    """
    Load data from a fixture file.
    
    Example:
        p8s loaddata fixtures/initial_data.json
        p8s loaddata data.yaml
    """
    import asyncio
    import json
    
    ensure_settings_module()
    
    if not fixture_file.exists():
        console.print(f"[red]Error:[/red] Fixture file not found: {fixture_file}")
        raise typer.Exit(1)
    
    async def _load():
        from p8s.core.settings import get_settings
        from p8s.db.session import init_db, close_db, SessionManager
        from p8s.admin.registry import get_model
        
        settings = get_settings()
        await init_db(settings.database)
        
        try:
            # Load fixture data
            content = fixture_file.read_text()
            
            if fixture_file.suffix in [".yaml", ".yml"]:
                try:
                    import yaml
                    data = yaml.safe_load(content)
                except ImportError:
                    console.print("[red]Error:[/red] YAML support requires 'pyyaml': pip install pyyaml")
                    raise typer.Exit(1)
            else:
                data = json.loads(content)
            
            if not isinstance(data, list):
                data = [data]
            
            loaded = 0
            
            async with SessionManager() as session:
                for item in data:
                    model_name = item.get("model")
                    fields = item.get("fields", {})
                    pk = item.get("pk")
                    
                    if not model_name:
                        console.print(f"[yellow]Warning:[/yellow] Skipping item without model field")
                        continue
                    
                    model = get_model(model_name)
                    if not model:
                        console.print(f"[yellow]Warning:[/yellow] Model not found: {model_name}")
                        continue
                    
                    # Include pk in fields if provided
                    if pk:
                        fields["id"] = pk
                    
                    try:
                        obj = model(**fields)
                        session.add(obj)
                        loaded += 1
                    except Exception as e:
                        console.print(f"[yellow]Warning:[/yellow] Error creating {model_name}: {e}")
                
                await session.commit()
            
            console.print(f"[green]✓[/green] Loaded {loaded} objects from {fixture_file}")
            
        finally:
            await close_db()
    
    asyncio.run(_load())


@app.command("dumpdata")
def dumpdata(
    output: Path = typer.Option(None, "--output", "-o", help="Output file path"),
    models: list[str] = typer.Option(None, "--model", "-m", help="Model names to dump"),
    format_type: str = typer.Option("json", "--format", "-f", help="Output format (json/yaml)"),
    indent: int = typer.Option(2, "--indent", help="Indentation level"),
):
    """
    Dump data to a fixture file.
    
    Example:
        p8s dumpdata -o fixtures/backup.json
        p8s dumpdata -m Product -m Category -o products.json
        p8s dumpdata --format yaml -o data.yaml
    """
    import asyncio
    import json
    
    ensure_settings_module()
    
    async def _dump():
        from p8s.core.settings import get_settings
        from p8s.db.session import init_db, close_db, SessionManager
        from p8s.admin.registry import get_registered_models, get_model
        from sqlalchemy import select
        
        settings = get_settings()
        await init_db(settings.database)
        
        try:
            fixtures = []
            
            async with SessionManager() as session:
                # Get models to dump
                if models:
                    model_list = [(name, get_model(name)) for name in models]
                    model_list = [(n, m) for n, m in model_list if m is not None]
                else:
                    model_list = list(get_registered_models().items())
                
                for model_name, model in model_list:
                    result = await session.execute(select(model))
                    items = result.scalars().all()
                    
                    for item in items:
                        fixture = {
                            "model": model_name,
                            "pk": str(item.id),
                            "fields": {},
                        }
                        
                        for field_name in model.model_fields.keys():
                            if field_name == "id":
                                continue
                            value = getattr(item, field_name, None)
                            
                            # Convert non-serializable types
                            if hasattr(value, "isoformat"):
                                value = value.isoformat()
                            elif hasattr(value, "__str__") and not isinstance(value, (str, int, float, bool, list, dict, type(None))):
                                value = str(value)
                            
                            fixture["fields"][field_name] = value
                        
                        fixtures.append(fixture)
                    
                    console.print(f"  Dumped {len(items)} {model_name} objects")
            
            # Format output
            if format_type == "yaml":
                try:
                    import yaml
                    output_str = yaml.dump(fixtures, default_flow_style=False, allow_unicode=True)
                except ImportError:
                    console.print("[red]Error:[/red] YAML support requires 'pyyaml': pip install pyyaml")
                    raise typer.Exit(1)
            else:
                output_str = json.dumps(fixtures, indent=indent, default=str)
            
            # Write or print
            if output:
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(output_str)
                console.print(f"[green]✓[/green] Dumped {len(fixtures)} objects to {output}")
            else:
                console.print(output_str)
                
        finally:
            await close_db()
    
    asyncio.run(_dump())

# ============================================================================
# CUSTOM COMMANDS - Discover and register app commands
# ============================================================================

def discover_app_commands() -> None:
    """
    Auto-discover custom management commands from installed apps.
    
    Looks for `management/commands/` directories in apps and registers
    any Typer commands found there.
    """
    import importlib
    import pkgutil
    
    try:
        from p8s.core.settings import get_settings
        settings = get_settings()
        
        for app_name in settings.installed_apps:
            commands_module_name = f"{app_name}.management.commands"
            
            try:
                commands_module = importlib.import_module(commands_module_name)
                package_path = getattr(commands_module, "__path__", None)
                
                if package_path:
                    for _, name, _ in pkgutil.iter_modules(package_path):
                        try:
                            cmd_module = importlib.import_module(
                                f"{commands_module_name}.{name}"
                            )
                            
                            # Look for a 'command' function or Typer app
                            if hasattr(cmd_module, "command"):
                                app.command(name)(cmd_module.command)
                            elif hasattr(cmd_module, "app"):
                                # If it's a Typer sub-app, add it
                                sub_app = cmd_module.app
                                if isinstance(sub_app, typer.Typer):
                                    app.add_typer(sub_app, name=name)
                        except Exception:
                            pass
            except ImportError:
                pass
    except Exception:
        pass


@app.command("run")
def run_command(
    command_name: str = typer.Argument(..., help="Command to run"),
    args: list[str] = typer.Argument(None, help="Command arguments"),
):
    """
    Run a custom management command.
    
    Example:
        p8s run my_command --arg1 value
        p8s run send_emails
    """
    import importlib
    
    ensure_settings_module()
    
    try:
        from p8s.core.settings import get_settings
        settings = get_settings()
        
        # Search for command in installed apps
        for app_name in settings.installed_apps:
            try:
                cmd_module = importlib.import_module(
                    f"{app_name}.management.commands.{command_name}"
                )
                
                if hasattr(cmd_module, "command"):
                    # Call the command function
                    import asyncio
                    result = cmd_module.command(*(args or []))
                    
                    # Handle async commands
                    if asyncio.iscoroutine(result):
                        asyncio.run(result)
                    
                    return
                    
            except ImportError:
                continue
        
        console.print(f"[red]Error:[/red] Command '{command_name}' not found")
        console.print("Make sure the command is in an app's management/commands/ directory")
        raise typer.Exit(1)
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("list-commands")
def list_commands():
    """
    List all available custom commands.
    
    Example:
        p8s list-commands
    """
    import importlib
    import pkgutil
    
    ensure_settings_module()
    
    console.print("[bold]Available Custom Commands:[/bold]")
    console.print()
    
    found_commands = []
    
    try:
        from p8s.core.settings import get_settings
        settings = get_settings()
        
        for app_name in settings.installed_apps:
            commands_module_name = f"{app_name}.management.commands"
            
            try:
                commands_module = importlib.import_module(commands_module_name)
                package_path = getattr(commands_module, "__path__", None)
                
                if package_path:
                    for _, name, _ in pkgutil.iter_modules(package_path):
                        try:
                            cmd_module = importlib.import_module(
                                f"{commands_module_name}.{name}"
                            )
                            
                            desc = getattr(cmd_module, "__doc__", "") or ""
                            if hasattr(cmd_module, "command"):
                                cmd_desc = getattr(cmd_module.command, "__doc__", "") or desc
                            else:
                                cmd_desc = desc
                            
                            found_commands.append({
                                "name": name,
                                "app": app_name,
                                "description": cmd_desc.strip().split("\n")[0] if cmd_desc else "",
                            })
                        except Exception:
                            pass
            except ImportError:
                pass
    except Exception:
        pass
    
    if not found_commands:
        console.print("[dim]No custom commands found.[/dim]")
        console.print()
        console.print("Create commands in your apps:")
        console.print("  backend/apps/myapp/management/commands/mycommand.py")
        return
    
    table = Table()
    table.add_column("Command", style="cyan")
    table.add_column("App")
    table.add_column("Description")
    
    for cmd in found_commands:
        table.add_row(cmd["name"], cmd["app"], cmd["description"])
    
    console.print(table)


# ============================================================================
# Main entry
# ============================================================================

def main():
    """Main entry point."""
    # Auto-discover custom commands
    try:
        discover_app_commands()
    except Exception:
        pass
    
    app()


if __name__ == "__main__":
    main()
