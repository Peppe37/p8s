"""
products models.
"""

from p8s import Model
from sqlmodel import Field


class Product(Model, table=True):
    """
    A product in the catalog.
    """
    __tablename__ = "products"

    name: str = Field(max_length=255, index=True)
    description: str | None = Field(default=None)
    price: float = Field(default=0.0)
    is_active: bool = Field(default=True)
    
    class Admin:
        list_display = ["name", "price", "is_active", "created_at"]
        search_fields = ["name", "description"]
        list_filter = ["is_active"]
