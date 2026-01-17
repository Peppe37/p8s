"""
P8s Multi-Database Session Management.

Provides utilities for working with multiple databases:
- Multi-database session factory
- Database-specific engine management
- Connection pooling per database

Example:
    ```python
    from p8s.db.multi import MultiDatabase

    db = MultiDatabase({
        "default": "postgresql://primary/db",
        "replica": "postgresql://replica/db",
    })

    async with db.session("replica") as session:
        # Read from replica
        users = await session.execute(select(User))
    ```
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


class MultiDatabase:
    """
    Manages multiple database connections.

    Example:
        ```python
        db = MultiDatabase({
            "default": "postgresql+asyncpg://localhost/primary",
            "analytics": "postgresql+asyncpg://localhost/analytics",
        })

        # Get session for specific database
        async with db.session("analytics") as session:
            await session.execute(query)
        ```
    """

    def __init__(
        self,
        databases: dict[str, str],
        echo: bool = False,
        pool_size: int = 5,
        max_overflow: int = 10,
    ):
        """
        Initialize multi-database manager.

        Args:
            databases: Dict mapping alias to connection URL
            echo: Enable SQL logging
            pool_size: Connection pool size per database
            max_overflow: Max pool overflow connections
        """
        self.databases = databases
        self.echo = echo
        self.pool_size = pool_size
        self.max_overflow = max_overflow

        self._engines: dict[str, AsyncEngine] = {}
        self._session_makers: dict[str, sessionmaker] = {}

    def get_engine(self, alias: str = "default") -> AsyncEngine:
        """
        Get or create engine for a database alias.

        Args:
            alias: Database alias

        Returns:
            AsyncEngine for the database

        Raises:
            KeyError: If alias not configured
        """
        if alias not in self._engines:
            if alias not in self.databases:
                raise KeyError(f"Database '{alias}' not configured")

            url = self.databases[alias]

            # Build engine kwargs - SQLite doesn't support pool_size
            engine_kwargs = {"echo": self.echo}

            # Only add pool parameters for non-SQLite databases
            if "sqlite" not in url.lower() and self.pool_size > 0:
                engine_kwargs["pool_size"] = self.pool_size
                engine_kwargs["max_overflow"] = self.max_overflow

            self._engines[alias] = create_async_engine(url, **engine_kwargs)

        return self._engines[alias]

    def get_session_maker(self, alias: str = "default") -> sessionmaker:
        """
        Get session maker for a database alias.

        Args:
            alias: Database alias

        Returns:
            Session maker configured for the database
        """
        if alias not in self._session_makers:
            engine = self.get_engine(alias)
            self._session_makers[alias] = sessionmaker(
                bind=engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )

        return self._session_makers[alias]

    @asynccontextmanager
    async def session(
        self,
        alias: str = "default",
    ) -> AsyncGenerator[AsyncSession, None]:
        """
        Get an async session for a specific database.

        Args:
            alias: Database alias

        Yields:
            Async database session

        Example:
            ```python
            async with db.session("replica") as session:
                result = await session.execute(select(User))
            ```
        """
        session_maker = self.get_session_maker(alias)
        async with session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def dispose_all(self) -> None:
        """Dispose all engine connections."""
        for engine in self._engines.values():
            await engine.dispose()
        self._engines.clear()
        self._session_makers.clear()


# Global instance for convenience
_multi_db: MultiDatabase | None = None


def configure_databases(databases: dict[str, str], **kwargs: Any) -> MultiDatabase:
    """
    Configure the global multi-database instance.

    Args:
        databases: Dict mapping alias to connection URL
        **kwargs: Additional options for MultiDatabase

    Returns:
        Configured MultiDatabase instance
    """
    global _multi_db
    _multi_db = MultiDatabase(databases, **kwargs)
    return _multi_db


def get_database(alias: str = "default") -> MultiDatabase:
    """
    Get the global multi-database instance.

    Args:
        alias: Not used, kept for compatibility

    Returns:
        Global MultiDatabase instance

    Raises:
        RuntimeError: If not configured
    """
    if _multi_db is None:
        raise RuntimeError(
            "Multi-database not configured. Call configure_databases() first."
        )
    return _multi_db


__all__ = [
    "MultiDatabase",
    "configure_databases",
    "get_database",
]
