"""
Database models for the demo application.

Showcases P8s features:
- UUID primary keys
- Automatic timestamps
- Soft delete
- AI-powered fields (AIField)
- Admin configuration
- Relationships
"""

from uuid import UUID
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from p8s import Model
from p8s.ai.fields import AIField, VectorField
from p8s.admin import register_model


@register_model
class Category(Model, table=True):
    """
    Product category.
    
    Simple model to demonstrate relationships.
    """
    
    __tablename__ = "categories"
    
    name: str = Field(max_length=100, unique=True, index=True)
    description: str | None = Field(default=None, max_length=500)
    
    # Relationship
    products: list["Product"] = Relationship(back_populates="category")
    
    class Admin:
        list_display = ["name", "description", "created_at"]
        search_fields = ["name", "description"]


@register_model
class Product(Model, table=True):
    """
    Product model.
    
    Demonstrates:
    - Basic fields
    - Foreign key relationship
    - AI-generated SEO description
    - Vector embeddings for similarity search
    """
    
    __tablename__ = "products"
    
    # Basic fields
    name: str = Field(max_length=255, index=True)
    description: str = Field(max_length=2000)
    price: float = Field(ge=0)
    stock: int = Field(default=0, ge=0)
    is_active: bool = Field(default=True)
    
    # Foreign key
    category_id: UUID | None = Field(default=None, foreign_key="categories.id")
    
    # Relationship
    category: Category | None = Relationship(back_populates="products")
    
    # AI-generated fields (requires p8s[ai])
    # Uncomment when AI is configured:
    # 
    # seo_description: str | None = AIField(
    #     prompt="Generate a compelling SEO description for this product: {name}. Description: {description}",
    #     source_fields=["name", "description"],
    #     default=None,
    # )
    # 
    # embedding: list[float] | None = VectorField(
    #     source_field="description",
    #     dimensions=1536,
    # )
    
    class Admin:
        list_display = ["name", "price", "stock", "is_active", "category_id"]
        search_fields = ["name", "description"]
        list_filter = ["is_active", "category_id"]
        ordering = ["-created_at"]


@register_model
class BlogPost(Model, table=True):
    """
    Blog post model.
    
    Demonstrates:
    - Text fields
    - Boolean flags
    - Author relationship (to User)
    - AI auto-summary
    """
    
    __tablename__ = "blog_posts"
    
    title: str = Field(max_length=255, index=True)
    slug: str | None = Field(default=None, max_length=255, unique=True)
    content: str = Field(max_length=50000)
    excerpt: str | None = Field(default=None, max_length=500)
    
    is_published: bool = Field(default=False)
    is_featured: bool = Field(default=False)
    
    # Author (User foreign key)
    author_id: UUID | None = Field(default=None, foreign_key="p8s_users.id")
    
    # AI-generated fields (requires p8s[ai])
    # Uncomment when AI is configured:
    #
    # auto_summary: str | None = AIField(
    #     prompt="Summarize this blog post in 2-3 sentences: {content}",
    #     source_fields=["content"],
    #     default=None,
    # )
    #
    # seo_title: str | None = AIField(
    #     prompt="Generate an SEO-optimized title for: {title}",
    #     source_fields=["title"],
    #     default=None,
    # )
    
    class Admin:
        list_display = ["title", "is_published", "is_featured", "author_id", "created_at"]
        search_fields = ["title", "content"]
        list_filter = ["is_published", "is_featured"]
        ordering = ["-created_at"]


@register_model
class Tag(Model, table=True):
    """
    Tag model for blog posts.
    """
    
    __tablename__ = "tags"
    
    name: str = Field(max_length=50, unique=True, index=True)
    color: str = Field(default="#3b82f6", max_length=7)  # Hex color
    
    class Admin:
        list_display = ["name", "color"]
        search_fields = ["name"]
