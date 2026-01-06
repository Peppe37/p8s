"""
P8s Admin Router - API endpoints for the admin panel.

These endpoints provide:
- Model introspection
- CRUD operations
- Search and filtering
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_, String
from sqlalchemy.ext.asyncio import AsyncSession

from p8s.admin.registry import (
    get_registered_models,
    get_model,
    get_model_metadata,
)
from p8s.auth.dependencies import require_admin
from p8s.auth.models import User
from p8s.core.settings import AdminSettings
from p8s.db.session import get_session


def create_admin_router(settings: AdminSettings) -> APIRouter:
    """
    Create the admin API router.
    
    Args:
        settings: Admin settings.
    
    Returns:
        Configured APIRouter.
    """
    router = APIRouter()
    
    @router.get("/")
    async def admin_index(
        user: User = Depends(require_admin),
    ) -> dict[str, Any]:
        """
        Get admin panel configuration.
        
        Returns:
            Admin settings and available models.
        """
        models = get_registered_models()
        
        return {
            "title": settings.title,
            "models": [
                get_model_metadata(model)
                for model in models.values()
            ],
        }
    
    @router.get("/models")
    async def list_models(
        user: User = Depends(require_admin),
    ) -> list[dict[str, Any]]:
        """
        List all registered models.
        
        Returns:
            List of model metadata.
        """
        models = get_registered_models()
        
        return [
            get_model_metadata(model)
            for model in models.values()
        ]
    
    @router.get("/models/{model_name}")
    async def get_model_info(
        model_name: str,
        user: User = Depends(require_admin),
    ) -> dict[str, Any]:
        """
        Get metadata for a specific model.
        
        Args:
            model_name: Name of the model.
        
        Returns:
            Model metadata.
        """
        model = get_model(model_name)
        
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        return get_model_metadata(model)
    
    @router.get("/models/{model_name}/items")
    async def list_items(
        model_name: str,
        skip: int = Query(0, ge=0),
        limit: int = Query(25, ge=1, le=1000),
        search: str | None = None,
        order_by: str | None = None,
        session: AsyncSession = Depends(get_session),
        user: User = Depends(require_admin),
    ) -> dict[str, Any]:
        """
        List items for a model with pagination and search.
        
        Args:
            model_name: Name of the model.
            skip: Offset for pagination.
            limit: Number of items per page.
            search: Search query.
            order_by: Field to order by (prefix with - for desc).
        
        Returns:
            Paginated list with total count.
        """
        model = get_model(model_name)
        
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        query = select(model)
        count_query = select(func.count()).select_from(model)
        
        # Apply soft delete filter if applicable
        if hasattr(model, "deleted_at"):
            query = query.where(model.deleted_at.is_(None))
            count_query = count_query.where(model.deleted_at.is_(None))
        
        # Apply search
        if search and hasattr(model, "Admin"):
            search_fields = getattr(model.Admin, "search_fields", [])
            if search_fields:
                conditions = []
                for field_name in search_fields:
                    if hasattr(model, field_name):
                        field = getattr(model, field_name)
                        conditions.append(
                            field.cast(String).ilike(f"%{search}%")
                        )
                if conditions:
                    query = query.where(or_(*conditions))
                    count_query = count_query.where(or_(*conditions))
        
        # Apply ordering
        if order_by:
            desc = order_by.startswith("-")
            field_name = order_by.lstrip("-")
            
            if hasattr(model, field_name):
                field = getattr(model, field_name)
                query = query.order_by(field.desc() if desc else field.asc())
        elif hasattr(model, "created_at"):
            query = query.order_by(model.created_at.desc())
        
        # Get total count
        count_result = await session.execute(count_query)
        total = count_result.scalar() or 0
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Execute query
        result = await session.execute(query)
        items = result.scalars().all()
        
        return {
            "items": [item.model_dump() for item in items],
            "total": total,
            "skip": skip,
            "limit": limit,
        }
    
    @router.get("/models/{model_name}/items/{item_id}")
    async def get_item(
        model_name: str,
        item_id: UUID,
        session: AsyncSession = Depends(get_session),
        user: User = Depends(require_admin),
    ) -> dict[str, Any]:
        """
        Get a single item by ID.
        
        Args:
            model_name: Name of the model.
            item_id: Item UUID.
        
        Returns:
            Item data.
        """
        model = get_model(model_name)
        
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        result = await session.execute(
            select(model).where(model.id == item_id)
        )
        item = result.scalar_one_or_none()
        
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        return item.model_dump()
    
    @router.post("/models/{model_name}/items", status_code=201)
    async def create_item(
        model_name: str,
        data: dict[str, Any],
        session: AsyncSession = Depends(get_session),
        user: User = Depends(require_admin),
    ) -> dict[str, Any]:
        """
        Create a new item.
        
        Args:
            model_name: Name of the model.
            data: Item data.
        
        Returns:
            Created item.
        """
        model = get_model(model_name)
        
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        # Remove readonly fields
        readonly = []
        if hasattr(model, "Admin"):
            readonly = getattr(model.Admin, "readonly_fields", [])
        
        clean_data = {k: v for k, v in data.items() if k not in readonly}
        
        try:
            item = model(**clean_data)
            session.add(item)
            await session.flush()
            await session.refresh(item)
            return item.model_dump()
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @router.patch("/models/{model_name}/items/{item_id}")
    async def update_item(
        model_name: str,
        item_id: UUID,
        data: dict[str, Any],
        session: AsyncSession = Depends(get_session),
        user: User = Depends(require_admin),
    ) -> dict[str, Any]:
        """
        Update an item.
        
        Args:
            model_name: Name of the model.
            item_id: Item UUID.
            data: Update data.
        
        Returns:
            Updated item.
        """
        model = get_model(model_name)
        
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        result = await session.execute(
            select(model).where(model.id == item_id)
        )
        item = result.scalar_one_or_none()
        
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        # Remove readonly fields
        readonly = ["id", "created_at"]
        if hasattr(model, "Admin"):
            readonly.extend(getattr(model.Admin, "readonly_fields", []))
        
        for key, value in data.items():
            if key not in readonly and hasattr(item, key):
                setattr(item, key, value)
        
        session.add(item)
        await session.flush()
        await session.refresh(item)
        
        return item.model_dump()
    
    @router.delete("/models/{model_name}/items/{item_id}")
    async def delete_item(
        model_name: str,
        item_id: UUID,
        hard: bool = False,
        session: AsyncSession = Depends(get_session),
        user: User = Depends(require_admin),
    ) -> dict[str, str]:
        """
        Delete an item.
        
        Args:
            model_name: Name of the model.
            item_id: Item UUID.
            hard: If True, permanently delete. Otherwise soft delete.
        
        Returns:
            Success message.
        """
        model = get_model(model_name)
        
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        result = await session.execute(
            select(model).where(model.id == item_id)
        )
        item = result.scalar_one_or_none()
        
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        if hard or not hasattr(item, "soft_delete"):
            await session.delete(item)
        else:
            item.soft_delete()
            session.add(item)
        
        await session.flush()
        
        return {"message": "Item deleted successfully"}
    
    return router
