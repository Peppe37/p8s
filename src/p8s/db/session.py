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

from p8s.core.settings import DatabaseSettings

# Global engine and session maker
_engine: AsyncEngine | None = None
_session_maker: async_sessionmaker[AsyncSession] | None = None

# Context variable for request-scoped sessions
_session_context: ContextVar[AsyncSession | None] = ContextVar(
    "session_context", default=None
)


async def init_db(settings: DatabaseSettings) -> None:
    """
    Initialize the database connection.
    
    Args:
        settings: Database settings.
    """
    global _engine, _session_maker
    
    _engine = create_async_engine(
        settings.url,
        echo=settings.echo,
        pool_size=settings.pool_size,
        max_overflow=settings.pool_overflow,
        pool_timeout=settings.pool_timeout,
    )
    
    _session_maker = async_sessionmaker(
        _engine,
        class_=AsyncSession,
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
    
    Use as a FastAPI dependency:
    
    ```python
    from p8s import get_session
    from sqlalchemy.ext.asyncio import AsyncSession
    
    @app.get("/items")
    async def get_items(session: AsyncSession = Depends(get_session)):
        result = await session.execute(select(Item))
        return result.scalars().all()
    ```
    
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
    
    Example:
        ```python
        async with SessionManager() as session:
            item = Item(name="test")
            session.add(item)
        ```
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
