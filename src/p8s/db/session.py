"""
P8s Session Management - Async database sessions.
"""

from collections.abc import AsyncGenerator
from contextvars import ContextVar
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlmodel import SQLModel

from p8s.ai.processor import process_ai_fields, process_vector_fields
from p8s.core.settings import DatabaseSettings

# Global engine and session maker
_engine: AsyncEngine | None = None
_session_maker: async_sessionmaker[AsyncSession] | None = None

# Context variable for request-scoped sessions
_session_context: ContextVar[AsyncSession | None] = ContextVar(
    "session_context", default=None
)


class P8sSession(AsyncSession):
    """
    Extended AsyncSession that handles AI field processing on commit.
    """

    async def commit(self) -> None:
        """Commit the current transaction, processing AI fields first."""
        # Process NEW objects
        for instance in self.new:
            if isinstance(instance, SQLModel):
                await process_ai_fields(instance)
                await process_vector_fields(instance)

        # Process DIRTY (updated) objects
        for instance in self.dirty:
            if isinstance(instance, SQLModel):
                # Note: This checks strictly if fields are missing or if forced.
                # Ideally, we should check if source fields changed using SA history.
                # For now, this ensures at least new fields (if cleared) are regenerated.
                await process_ai_fields(instance)
                await process_vector_fields(instance)

        await super().commit()


async def init_db(settings: DatabaseSettings) -> None:
    """
    Initialize the database connection.

    Args:
        settings: Database settings.
    """
    global _engine, _session_maker

    # Prepare engine arguments
    connect_args = {}
    engine_args = {
        "echo": settings.echo,
        "pool_size": settings.pool_size,
        "max_overflow": settings.pool_overflow,
        "pool_timeout": settings.pool_timeout,
    }

    # Handle SQLite specific limitations (no pool args supported with StatcPool usually,
    # but more importantly aiosqlite interface issues)
    if "sqlite" in str(settings.url):
        # Remove pool arguments for SQLite as they are not supported by the default pool or aiosqlite in some contexts
        engine_args.pop("pool_size", None)
        engine_args.pop("max_overflow", None)
        engine_args.pop("pool_timeout", None)

        # Enable foreign keys for SQLite
        connect_args["check_same_thread"] = False

    _engine = create_async_engine(
        settings.url,
        connect_args=connect_args,
        **engine_args,
    )

    _session_maker = async_sessionmaker(
        _engine,
        class_=P8sSession,  # Use custom session
        expire_on_commit=False,
        autoflush=False,
    )


async def close_db() -> None:
    """Close the database connection."""
    global _engine

    if _engine:
        await _engine.dispose()
        _engine = None


async def create_all_tables() -> None:
    """
    Create all tables in the database.

    WARNING: Use only for development. Use migrations in production.
    """
    global _engine

    if _engine:
        async with _engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)


async def drop_all_tables() -> None:
    """
    Drop all tables in the database.

    WARNING: This is destructive! Use with caution.
    """
    global _engine

    if _engine:
        async with _engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.drop_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get an async database session.

    Use as a FastAPI dependency.

    Yields:
        AsyncSession: Database session.
    """
    if _session_maker is None:
        raise RuntimeError(
            "Database not initialized. Call init_db() first or use P8sApp."
        )

    async with _session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_engine() -> AsyncEngine:
    """
    Get the database engine.

    Returns:
        AsyncEngine: The SQLAlchemy async engine.

    Raises:
        RuntimeError: If database is not initialized.
    """
    if _engine is None:
        raise RuntimeError(
            "Database not initialized. Call init_db() first or use P8sApp."
        )
    return _engine


class SessionManager:
    """
    Context manager for manual session handling.
    """

    def __init__(self) -> None:
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> AsyncSession:
        if _session_maker is None:
            raise RuntimeError("Database not initialized.")

        self._session = _session_maker()
        return self._session

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        if self._session:
            if exc_type:
                await self._session.rollback()
            else:
                await self._session.commit()
            await self._session.close()
