"""
demo_p8s - A P8s Demo Application

This demo showcases all P8s features:
- Model with UUID, timestamps, soft delete
- AI-powered fields
- Authentication
- Admin panel API
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends, HTTPException, FastAPI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from p8s import P8sApp, get_session
from p8s.auth.router import router as auth_router
from p8s.auth.dependencies import get_current_user, require_auth
from p8s.auth.models import User
from p8s.admin import register_model
from p8s.db.session import init_db, close_db, get_engine
from p8s.core.settings import get_settings

# Import models to register them (this registers their tables)
from backend.models import Product, Category, BlogPost, Tag


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Custom lifespan to initialize database and create tables."""
    settings = get_settings()
    
    # Initialize database
    await init_db(settings.database)
    
    # Create all tables (for demo - use migrations in production!)
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    print("🔥 P8s Demo started! Tables created.")
    
    yield
    
    # Shutdown
    await close_db()
    print("👋 P8s Demo stopped.")


# Create the app with custom lifespan
app = P8sApp(
    title="P8s Demo",
    description="🔥 A demo application showcasing P8s framework features",
    version="0.1.0",
    lifespan=lifespan,
)

# Include auth routes
app.include_router(auth_router, prefix="/api", tags=["auth"])



# ============================================================================
# Public endpoints
# ============================================================================

@app.get("/")
async def root():
    """Welcome endpoint."""
    return {
        "message": "Welcome to P8s Demo! 🔥",
        "docs": "/docs",
        "admin": "/admin",
    }


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "framework": "P8s"}


# ============================================================================
# Products API
# ============================================================================

@app.get("/api/products")
async def list_products(
    skip: int = 0,
    limit: int = 10,
    session: AsyncSession = Depends(get_session),
):
    """List all products."""
    result = await session.execute(
        select(Product)
        .where(Product.deleted_at.is_(None))
        .offset(skip)
        .limit(limit)
    )
    products = result.scalars().all()
    return [p.model_dump() for p in products]


@app.get("/api/products/{product_id}")
async def get_product(
    product_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Get a single product."""
    from uuid import UUID
    
    result = await session.execute(
        select(Product).where(Product.id == UUID(product_id))
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return product.model_dump()


@app.post("/api/products", status_code=201)
async def create_product(
    name: str,
    description: str,
    price: float,
    category_id: str | None = None,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_auth),
):
    """Create a new product (requires auth)."""
    from uuid import UUID
    
    product = Product(
        name=name,
        description=description,
        price=price,
        category_id=UUID(category_id) if category_id else None,
    )
    
    session.add(product)
    await session.flush()
    await session.refresh(product)
    
    return product.model_dump()


# ============================================================================
# Categories API
# ============================================================================

@app.get("/api/categories")
async def list_categories(
    session: AsyncSession = Depends(get_session),
):
    """List all categories."""
    result = await session.execute(
        select(Category).where(Category.deleted_at.is_(None))
    )
    categories = result.scalars().all()
    return [c.model_dump() for c in categories]


@app.post("/api/categories", status_code=201)
async def create_category(
    name: str,
    description: str | None = None,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_auth),
):
    """Create a new category (requires auth)."""
    category = Category(name=name, description=description)
    
    session.add(category)
    await session.flush()
    await session.refresh(category)
    
    return category.model_dump()


# ============================================================================
# Blog API
# ============================================================================

@app.get("/api/blog")
async def list_posts(
    published: bool = True,
    skip: int = 0,
    limit: int = 10,
    session: AsyncSession = Depends(get_session),
):
    """List blog posts."""
    query = select(BlogPost).where(BlogPost.deleted_at.is_(None))
    
    if published:
        query = query.where(BlogPost.is_published == True)
    
    query = query.offset(skip).limit(limit)
    
    result = await session.execute(query)
    posts = result.scalars().all()
    return [p.model_dump() for p in posts]


@app.post("/api/blog", status_code=201)
async def create_post(
    title: str,
    content: str,
    is_published: bool = False,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_auth),
):
    """Create a blog post (requires auth)."""
    post = BlogPost(
        title=title,
        content=content,
        is_published=is_published,
        author_id=user.id,
    )
    
    session.add(post)
    await session.flush()
    await session.refresh(post)
    
    return post.model_dump()


# ============================================================================
# User profile
# ============================================================================

@app.get("/api/me")
async def get_me(user: User | None = Depends(get_current_user)):
    """Get current user profile."""
    if user:
        return {
            "authenticated": True,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role.value,
            }
        }
    return {"authenticated": False, "user": None}
