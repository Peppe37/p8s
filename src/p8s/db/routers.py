"""
P8s Database Routers - Multi-database routing support.

Provides Django-style database routing for:
- Read/write splitting (primary/replica)
- Model-based routing
- Custom routing logic

Example:
    ```python
    from p8s.db.routers import ReadReplicaRouter

    class AppSettings(Settings):
        databases = {
            "default": "postgresql://primary...",
            "replica": "postgresql://replica...",
        }
        database_routers = [ReadReplicaRouter]
    ```
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlmodel import SQLModel


class DatabaseRouter(ABC):
    """
    Abstract base class for database routers.

    Subclass this to implement custom routing logic.
    """

    @abstractmethod
    def db_for_read(self, model: type["SQLModel"], **hints: Any) -> str | None:
        """
        Return the database alias for read operations.

        Args:
            model: The model class being queried
            **hints: Additional hints (e.g., instance)

        Returns:
            Database alias string or None for default
        """
        pass

    @abstractmethod
    def db_for_write(self, model: type["SQLModel"], **hints: Any) -> str | None:
        """
        Return the database alias for write operations.

        Args:
            model: The model class being written
            **hints: Additional hints (e.g., instance)

        Returns:
            Database alias string or None for default
        """
        pass

    def allow_migrate(
        self,
        db: str,
        model: type["SQLModel"],
        **hints: Any,
    ) -> bool | None:
        """
        Determine if a model should be migrated on a database.

        Args:
            db: Database alias
            model: Model class
            **hints: Additional hints

        Returns:
            True to allow, False to deny, None for no opinion
        """
        return None


class ReadReplicaRouter(DatabaseRouter):
    """
    Routes read queries to replica, writes to primary.

    This is the most common multi-database pattern for
    scaling read-heavy applications.

    Example:
        ```python
        from p8s.db.routers import ReadReplicaRouter

        # In settings
        databases = {
            "default": "postgresql://primary/db",
            "replica": "postgresql://replica/db",
        }
        database_routers = [ReadReplicaRouter(replica_alias="replica")]
        ```
    """

    def __init__(
        self,
        primary_alias: str = "default",
        replica_alias: str = "replica",
    ):
        """
        Initialize router.

        Args:
            primary_alias: Database alias for primary (writes)
            replica_alias: Database alias for replica (reads)
        """
        self.primary_alias = primary_alias
        self.replica_alias = replica_alias

    def db_for_read(self, model: type["SQLModel"], **hints: Any) -> str:
        """Return replica for all reads."""
        return self.replica_alias

    def db_for_write(self, model: type["SQLModel"], **hints: Any) -> str:
        """Return primary for all writes."""
        return self.primary_alias

    def allow_migrate(
        self,
        db: str,
        model: type["SQLModel"],
        **hints: Any,
    ) -> bool | None:
        """Only allow migrations on primary."""
        if db == self.primary_alias:
            return True
        if db == self.replica_alias:
            return False
        return None


class ModelRouter(DatabaseRouter):
    """
    Routes based on model configuration.

    Each model can specify its database in its Meta/Admin class.

    Example:
        ```python
        class User(Model, table=True):
            class Admin:
                database = "users_db"

        router = ModelRouter()
        # User queries will go to "users_db"
        ```
    """

    def _get_model_db(self, model: type["SQLModel"]) -> str | None:
        """Get database from model configuration."""
        if hasattr(model, "Admin") and hasattr(model.Admin, "database"):
            return model.Admin.database
        return None

    def db_for_read(self, model: type["SQLModel"], **hints: Any) -> str | None:
        """Return model-specific database."""
        return self._get_model_db(model)

    def db_for_write(self, model: type["SQLModel"], **hints: Any) -> str | None:
        """Return model-specific database."""
        return self._get_model_db(model)


class RouterChain:
    """
    Chains multiple routers together.

    Routers are consulted in order. First non-None response wins.

    Example:
        ```python
        chain = RouterChain([
            ModelRouter(),      # Check model-specific first
            ReadReplicaRouter(), # Fallback to read/write split
        ])
        db = chain.db_for_read(User)
        ```
    """

    def __init__(self, routers: list[DatabaseRouter]):
        """
        Initialize with list of routers.

        Args:
            routers: List of DatabaseRouter instances
        """
        self.routers = routers

    def db_for_read(self, model: type["SQLModel"], **hints: Any) -> str:
        """Get database for read, consulting routers in order."""
        for router in self.routers:
            db = router.db_for_read(model, **hints)
            if db is not None:
                return db
        return "default"

    def db_for_write(self, model: type["SQLModel"], **hints: Any) -> str:
        """Get database for write, consulting routers in order."""
        for router in self.routers:
            db = router.db_for_write(model, **hints)
            if db is not None:
                return db
        return "default"


__all__ = [
    "DatabaseRouter",
    "ReadReplicaRouter",
    "ModelRouter",
    "RouterChain",
]
