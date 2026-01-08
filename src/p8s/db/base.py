"""
P8s Base Model - The foundation for all P8s models.

Combines SQLModel with P8s-specific features like admin configuration
and AI field support.
"""

from datetime import datetime, timezone
from typing import Any, ClassVar
from uuid import UUID, uuid4

from pydantic import ConfigDict
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)

class AdminConfig:
    """
    Admin panel configuration for a model.
    
    Example:
        ```python
        class Product(Model):
            class Admin:
                list_display = ["name", "price"]
                search_fields = ["name", "description"]
                ordering = ["-created_at"]
                actions = ["mark_active", "mark_inactive", "export_csv"]
        ```
    """
    
    # Fields to display in list view
    list_display: list[str] = []
    
    # Fields that are searchable
    search_fields: list[str] = []
    
    # Default ordering
    ordering: list[str] = []
    
    # Fields to filter by
    list_filter: list[str] = []
    
    # Fields editable in list view
    list_editable: list[str] = []
    
    # Read-only fields
    readonly_fields: list[str] = []
    
    # Exclude from admin
    exclude: list[str] = []
    
    # Fieldsets for detail view
    fieldsets: list[tuple[str, dict[str, Any]]] = []
    
    # Admin actions (bulk operations)
    actions: list[str] = []
    
    # Inline models for editing related objects
    inlines: list[Any] = []


class Model(SQLModel):
    """
    Base model for all P8s models.
    
    Provides:
    - UUID primary key
    - Automatic timestamps
    - Admin configuration
    - Soft delete support
    - AI field integration
    
    Example:
        ```python
        from p8s import Model
        from sqlmodel import Field
        
        class Product(Model, table=True):
            name: str = Field(max_length=255)
            price: float = Field(ge=0)
            description: str | None = None
        ```
    """
    
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
    )
    
    # Primary key - UUID by default
    id: UUID | None = Field(
        default_factory=uuid4,
        primary_key=True,
        description="Unique identifier",
    )
    
    # Timestamps
    created_at: datetime | None = Field(
        default_factory=utc_now,
        description="Creation timestamp",
    )
    updated_at: datetime | None = Field(
        default_factory=utc_now,
        sa_column_kwargs={"onupdate": utc_now},
        description="Last update timestamp",
    )
    
    # Soft delete
    deleted_at: datetime | None = Field(
        default=None,
        description="Deletion timestamp (soft delete)",
    )
    
    # Admin configuration (class variable, not a field)
    Admin: ClassVar[type[AdminConfig]] = AdminConfig
    
    def soft_delete(self) -> None:
        """Mark the record as deleted."""
        self.deleted_at = utc_now()
    
    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.deleted_at = None
    
    @property
    def is_deleted(self) -> bool:
        """Check if record is soft-deleted."""
        return self.deleted_at is not None
    
    def to_dict(self, exclude: set[str] | None = None) -> dict[str, Any]:
        """
        Convert model to dictionary.
        
        Args:
            exclude: Fields to exclude.
        
        Returns:
            Dictionary representation.
        """
        exclude = exclude or set()
        return {
            k: v for k, v in self.model_dump().items()
            if k not in exclude
        }
    
    @classmethod
    def get_admin_config(cls) -> AdminConfig:
        """Get admin configuration for this model."""
        if hasattr(cls, "Admin") and cls.Admin is not AdminConfig:
            config = AdminConfig()
            for key in dir(cls.Admin):
                if not key.startswith("_"):
                    setattr(config, key, getattr(cls.Admin, key))
            return config
        return AdminConfig()
    
    @classmethod
    def get_table_name(cls) -> str:
        """Get the database table name."""
        return cls.__tablename__ if hasattr(cls, "__tablename__") else cls.__name__.lower()


class TimestampMixin(SQLModel):
    """
    Mixin that adds only timestamp fields.
    
    Use when you need custom primary key handling.
    """
    
    created_at: datetime | None = Field(
        default_factory=utc_now,
    )
    updated_at: datetime | None = Field(
        default_factory=utc_now,
        sa_column_kwargs={"onupdate": utc_now},
    )


class SoftDeleteMixin(SQLModel):
    """
    Mixin that adds soft delete capability.
    """
    
    deleted_at: datetime | None = Field(default=None)
    
    def soft_delete(self) -> None:
        self.deleted_at = utc_now()
    
    def restore(self) -> None:
        self.deleted_at = None
    
    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
