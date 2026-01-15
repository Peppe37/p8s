"""
P8s Migrations - Alembic wrapper for easy migrations.
"""

from pathlib import Path
from typing import Any

from alembic import command
from alembic.config import Config as AlembicConfig
from alembic.script import ScriptDirectory

from p8s.core.settings import get_settings


def get_alembic_config(
    migrations_dir: Path | str | None = None,
) -> AlembicConfig:
    """
    Get Alembic configuration.

    Args:
        migrations_dir: Path to migrations directory.
                       Defaults to ./migrations in project root.

    Returns:
        Configured AlembicConfig.
    """
    settings = get_settings()

    if migrations_dir is None:
        migrations_dir = Path(settings.base_dir) / "migrations"

    migrations_dir = Path(migrations_dir)

    # Create Alembic config
    alembic_cfg = AlembicConfig()

    # Set script location
    alembic_cfg.set_main_option("script_location", str(migrations_dir))

    # Set database URL (convert async URL to sync for Alembic)
    db_url = settings.database.url

    # Convert async drivers to sync for Alembic
    if "+aiosqlite" in db_url:
        db_url = db_url.replace("+aiosqlite", "")
    elif "+asyncpg" in db_url:
        db_url = db_url.replace("+asyncpg", "+psycopg2")

    alembic_cfg.set_main_option("sqlalchemy.url", db_url)

    return alembic_cfg


def init_migrations(
    migrations_dir: Path | str | None = None,
) -> None:
    """
    Initialize migrations directory.

    Creates the migrations folder with Alembic configuration.

    Args:
        migrations_dir: Path to migrations directory.
    """
    settings = get_settings()

    if migrations_dir is None:
        migrations_dir = Path(settings.base_dir) / "migrations"

    migrations_dir = Path(migrations_dir)

    if migrations_dir.exists():
        raise FileExistsError(f"Migrations directory already exists: {migrations_dir}")

    migrations_dir.mkdir(parents=True)

    # Create alembic.ini content
    alembic_ini = f"""# P8s Migrations Configuration
[alembic]
script_location = {migrations_dir}
prepend_sys_path = .
version_path_separator = os

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""
    (settings.base_dir / "alembic.ini").write_text(alembic_ini)

    # Create env.py
    env_py = '''"""
Alembic environment configuration for P8s.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

# Import P8s framework models (User, permissions, etc.)
from p8s.auth.models import User
from p8s.auth.permissions import UserPermissionLink, UserGroupLink

# Auto-discover models from installed apps
from p8s.core.settings import get_settings
import importlib

settings = get_settings()
for app_name in getattr(settings, 'installed_apps', []):
    try:
        importlib.import_module(f"{app_name}.models")
    except ImportError:
        pass

# Explicitly import project models (backend.models)
# This ensures models are discovered even without installed_apps config
try:
    import backend.models  # noqa: F401
except ImportError:
    pass

# This is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# SQLModel metadata
target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''
    (migrations_dir / "env.py").write_text(env_py)

    # Create script.py.mako template
    script_mako = '''"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
'''
    (migrations_dir / "script.py.mako").write_text(script_mako)

    # Create versions directory
    (migrations_dir / "versions").mkdir()
    (migrations_dir / "versions" / "__init__.py").write_text("")


def create_migration(
    message: str,
    autogenerate: bool = True,
    migrations_dir: Path | str | None = None,
) -> str:
    """
    Create a new migration.

    Args:
        message: Migration message/description.
        autogenerate: Auto-detect model changes.
        migrations_dir: Path to migrations directory.

    Returns:
        Path to the new migration file.
    """
    alembic_cfg = get_alembic_config(migrations_dir)

    if autogenerate:
        command.revision(alembic_cfg, message=message, autogenerate=True)
    else:
        command.revision(alembic_cfg, message=message)

    # Get the latest revision file
    script_dir = ScriptDirectory.from_config(alembic_cfg)
    head = script_dir.get_current_head()

    return head or ""


def run_migrations(
    revision: str = "head",
    migrations_dir: Path | str | None = None,
) -> None:
    """
    Run migrations up to a specific revision.

    Args:
        revision: Target revision (default: "head" for latest).
        migrations_dir: Path to migrations directory.
    """
    alembic_cfg = get_alembic_config(migrations_dir)
    command.upgrade(alembic_cfg, revision)


def rollback_migration(
    revision: str = "-1",
    migrations_dir: Path | str | None = None,
) -> None:
    """
    Rollback migrations.

    Args:
        revision: Target revision (default: "-1" for previous).
        migrations_dir: Path to migrations directory.
    """
    alembic_cfg = get_alembic_config(migrations_dir)
    command.downgrade(alembic_cfg, revision)


def show_migrations(
    migrations_dir: Path | str | None = None,
) -> list[dict[str, Any]]:
    """
    Show migration history.

    Args:
        migrations_dir: Path to migrations directory.

    Returns:
        List of migration info dicts.
    """
    alembic_cfg = get_alembic_config(migrations_dir)
    script_dir = ScriptDirectory.from_config(alembic_cfg)

    migrations = []
    for rev in script_dir.walk_revisions():
        migrations.append(
            {
                "revision": rev.revision,
                "down_revision": rev.down_revision,
                "message": rev.doc,
                "path": rev.path,
            }
        )

    return migrations


def get_current_revision(
    migrations_dir: Path | str | None = None,
) -> str | None:
    """
    Get current database revision.

    Args:
        migrations_dir: Path to migrations directory.

    Returns:
        Current revision ID or None.
    """
    alembic_cfg = get_alembic_config(migrations_dir)
    script_dir = ScriptDirectory.from_config(alembic_cfg)

    return script_dir.get_current_head()
