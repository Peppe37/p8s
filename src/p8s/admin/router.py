"""
P8s Admin Router - API endpoints for the admin panel.

These endpoints provide:
- Model introspection
- CRUD operations
- Search and filtering

Like Django: /admin/ serves the UI, /admin/api/ contains the REST endpoints.
"""

from typing import Any
from uuid import UUID

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from starlette.responses import FileResponse, HTMLResponse
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
    # Auto-discover models from installed apps
    from p8s.admin.registry import auto_discover_models
    auto_discover_models()

    router = APIRouter()
    static_dir = Path(__file__).parent / "static"

    # =========================================================================
    # Static Files Serving - No auth required (frontend handles auth)
    # =========================================================================

    @router.get("/", include_in_schema=False)
    async def admin_root():
        """Serve the admin UI entry point (like Django /admin/)."""
        index_path = static_dir / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        return HTMLResponse("<h1>Admin UI not built</h1><p>Running in headless mode.</p>", status_code=404)

    @router.get("/assets/{path:path}", include_in_schema=False)
    async def admin_assets(path: str):
        """Serve static assets."""
        file_path = static_dir / "assets" / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return HTMLResponse("Not Found", status_code=404)

    # =========================================================================
    # API Endpoints - All require admin auth
    # =========================================================================

    @router.get("/api/config")
    async def admin_config(
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

    @router.get("/{model_name}")
    async def list_items(
        model_name: str,
        page: int = Query(1, ge=1),
        page_size: int = Query(25, ge=1, le=1000),
        search: str | None = None,
        order_by: str | None = None,
        request: Request = None,  # Added Request to access dynamic query params
        session: AsyncSession = Depends(get_session),
        user: User = Depends(require_admin),
    ) -> dict[str, Any]:
        """
        List items for a model with pagination and search.

        Args:
            model_name: Name of the model.
            page: Page number (1-indexed).
            page_size: Number of items per page.
            search: Search query.
            order_by: Field to order by (prefix with - for desc).

        Returns:
            Paginated list with total count.
        """
        model = get_model(model_name)

        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        skip = (page - 1) * page_size

        query = select(model)
        count_query = select(func.count()).select_from(model)

        # Apply soft delete filter if applicable
        if hasattr(model, "deleted_at"):
            query = query.where(model.deleted_at.is_(None))
            count_query = count_query.where(model.deleted_at.is_(None))

        # Apply exact match filters from query params (if in list_filter)
        if hasattr(model, "Admin") and hasattr(model.Admin, "list_filter"):
            list_filter = getattr(model.Admin, "list_filter", [])
            query_params = request.query_params if request else {}
            
            for field_name in list_filter:
                value = query_params.get(field_name)
                if value is None:
                    continue

                target_field = None
                
                # Check if model has the field
                if hasattr(model, field_name):
                    field = getattr(model, field_name)
                    
                    # Detect if it is a Relationship
                    is_relation = False
                    if hasattr(field, "property"):
                        prop_type = type(field.property).__name__
                        if "Relationship" in prop_type:
                            is_relation = True
                    
                    if is_relation:
                        # If relation, try to use the _id field (Foreign Key)
                        # This assumes standard naming convention (name -> name_id)
                        fk_name = f"{field_name}_id"
                        if hasattr(model, fk_name):
                            target_field = getattr(model, fk_name)
                    else:
                        # Normal field
                        target_field = field
                
                # Fallback: Check if field_name_id exists directly
                elif hasattr(model, f"{field_name}_id"):
                    target_field = getattr(model, f"{field_name}_id")
                
                if target_field is not None:
                    # Handle Boolean conversion
                    # SQLAlchemy/SQLModel might not automatically convert "true"/"false" strings
                    if hasattr(target_field, "type") and type(target_field.type).__name__ == "Boolean":
                        if str(value).lower() in ("true", "1", "yes"):
                            value = True
                        elif str(value).lower() in ("false", "0", "no"):
                            value = False
                            
                    # Handle UUID conversion
                    # If the field expects a UUID, we must convert the string
                    if hasattr(target_field, "type"):
                        type_name = type(target_field.type).__name__
                        # Check for various UUID type representations (Uuid, GUID, etc)
                        if "Uuid" in type_name or "GUID" in type_name:
                            try:
                                if isinstance(value, str):
                                    value = UUID(value)
                            except (ValueError, TypeError):
                                # If invalid UUID, ignore this filter or let it fail?
                                # Let's ignore to prevent crash, effectively filtering by nothing (or let it fail if STRICT)
                                # Better to just pass it through or skip? passing str to uuid field crashes as seen.
                                # So if invalid, we skip filtering.
                                continue

                    # Apply filter
                    query = query.where(target_field == value)
                    count_query = count_query.where(target_field == value)

        # Apply ordering
        if order_by:
            desc = order_by.startswith("-")
            field_name = order_by.lstrip("-")

            if hasattr(model, field_name):
                field = getattr(model, field_name)
                
                # Safe sort: ignore relationships for now to avoid 500 errors
                # We check if it is a RelationshipProperty (by checking for 'mapper' or 'entity')
                # Or simply try/except the sort construction
                try:
                   # Check if it's a relationship by inspecting property
                   is_relation = False
                   if hasattr(field, "property"):
                       prop_type = type(field.property).__name__
                       if "Relationship" in prop_type:
                           is_relation = True
                   
                   if not is_relation:
                       query = query.order_by(field.desc() if desc else field.asc())
                except Exception:
                   pass
        elif hasattr(model, "created_at"):
            query = query.order_by(model.created_at.desc())

        # Get total count
        count_result = await session.execute(count_query)
        total = count_result.scalar() or 0

        # Eager load relationships if they are in list_display
        # We need to know which fields are relations. We can check the model metadata.
        from sqlalchemy.orm import selectinload
        
        metadata = get_model_metadata(model)
        relations_to_load = []
        
        # Check list_display from Admin config
        list_display = []
        if hasattr(model, "Admin") and hasattr(model.Admin, "list_display"):
            list_display = getattr(model.Admin, "list_display")
            
        for field_name in list_display:
            if field_name in metadata["fields"]:
                field_meta = metadata["fields"][field_name]
                if field_meta.get("type") == "relation" and field_name != "id":
                    # It's a relation to be displayed
                    if hasattr(model, field_name):
                        relations_to_load.append(getattr(model, field_name))

        if relations_to_load:
            for rel in relations_to_load:
                query = query.options(selectinload(rel))
        
        # Apply pagination
        query = query.offset(skip).limit(page_size)

        # Execute query
        result = await session.execute(query)
        items = result.scalars().all()
        
        # Serialize items, including relation string refs
        final_items = []
        for item in items:
            data = item.model_dump()
            
            # Inject relation string representations
            for rel_field in list_display:
                if rel_field in metadata["fields"] and metadata["fields"][rel_field].get("type") == "relation":
                    rel_val = getattr(item, rel_field, None)
                    if rel_val:
                        # Try __str__ or some reasonable default
                        data[rel_field] = str(rel_val)
                        
                        # If the relation object has a 'name' or 'title', use that preference
                        if hasattr(rel_val, "name"):
                            data[rel_field] = rel_val.name
                        elif hasattr(rel_val, "title"):
                            data[rel_field] = rel_val.title
                    else:
                         data[rel_field] = None

            final_items.append(data)

        return {
            "items": final_items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    @router.get("/{model_name}/{item_id}")
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

    @router.post("/{model_name}", status_code=201)
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

    @router.patch("/{model_name}/{item_id}")
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

    @router.delete("/{model_name}/{item_id}")
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

    @router.post("/{model_name}/bulk-delete")
    async def bulk_delete(
        model_name: str,
        data: dict[str, Any],
        session: AsyncSession = Depends(get_session),
        user: User = Depends(require_admin),
    ) -> dict[str, int]:
        """
        Bulk delete items.

        Args:
            model_name: Name of the model.
            data: Dictionary with 'ids' list.

        Returns:
            Number of deleted items.
        """
        model = get_model(model_name)

        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        ids = data.get("ids", [])
        deleted = 0

        for item_id in ids:
            try:
                uuid_id = UUID(item_id) if isinstance(item_id, str) else item_id
                result = await session.execute(
                    select(model).where(model.id == uuid_id)
                )
                item = result.scalar_one_or_none()
                if item:
                    if hasattr(item, "soft_delete"):
                        item.soft_delete()
                        session.add(item)
                    else:
                        await session.delete(item)
                    deleted += 1
            except Exception:
                pass

        await session.flush()
        return {"deleted": deleted}

    @router.post("/{model_name}/action")
    async def execute_action_endpoint(
        model_name: str,
        data: dict[str, Any],
        session: AsyncSession = Depends(get_session),
        user: User = Depends(require_admin),
    ) -> dict[str, Any]:
        """
        Execute an admin action.

        Args:
            model_name: Name of the model.
            data: Payload containing 'action' name and 'ids' list.

        Returns:
            Action result.
        """
        from p8s.admin.actions import execute_action

        action_name = data.get("action")
        ids = data.get("ids", [])

        if not action_name:
            raise HTTPException(status_code=400, detail="Action name required")

        try:
            # Convert string IDs to UUIDs if necessary
            # The frontend sends strings, backend mostly expects UUIDs for ID fields
            # We try to convert, but let execute_action handle validation
            uuid_ids = []
            for id_str in ids:
                try:
                    uuid_ids.append(UUID(id_str) if isinstance(id_str, str) else id_str)
                except ValueError:
                    continue
            
            return await execute_action(model_name, action_name, session, uuid_ids)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))

    return router

