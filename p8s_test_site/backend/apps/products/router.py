"""
products API routes.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from p8s.db.session import get_session

router = APIRouter()


@router.get("/")
async def list_products(
    session: AsyncSession = Depends(get_session),
):
    from sqlmodel import select
    from backend.apps.products.models import Product
    
    result = await session.execute(select(Product))
    return result.scalars().all()
