"""
P8s CRUD - Generic CRUD operations.

Inspired by FastAPI-CRUD but integrated with P8s models.
"""

from typing import Any, Generic, TypeVar
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from p8s.db.session import get_session

ModelType = TypeVar("ModelType", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base class for CRUD operations.

    Example:
        ```python
        from p8s.db.crud import CRUDBase

        class ProductCRUD(CRUDBase[Product, ProductCreate, ProductUpdate]):
            pass

        product_crud = ProductCRUD(Product)
        ```
    """

    def __init__(self, model: type[ModelType]) -> None:
        """
        Initialize CRUD operations.

        Args:
            model: The SQLModel class.
        """
        self.model = model

    async def get(
        self,
        session: AsyncSession,
        id: UUID,
    ) -> ModelType | None:
        """
        Get a single record by ID.

        Args:
            session: Database session.
            id: Record ID.

        Returns:
            The record or None.
        """
        result = await session.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_or_404(
        self,
        session: AsyncSession,
        id: UUID,
    ) -> ModelType:
        """
        Get a single record by ID or raise 404.

        Args:
            session: Database session.
            id: Record ID.

        Returns:
            The record.

        Raises:
            HTTPException: If not found.
        """
        obj = await self.get(session, id)
        if not obj:
            raise HTTPException(
                status_code=404,
                detail=f"{self.model.__name__} not found",
            )
        return obj

    async def list(
        self,
        session: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False,
    ) -> list[ModelType]:
        """
        Get a list of records.

        Args:
            session: Database session.
            skip: Number of records to skip.
            limit: Maximum number of records.
            include_deleted: Include soft-deleted records.

        Returns:
            List of records.
        """
        query = select(self.model)

        # Filter soft-deleted if model has deleted_at
        if hasattr(self.model, "deleted_at") and not include_deleted:
            query = query.where(self.model.deleted_at.is_(None))

        query = query.offset(skip).limit(limit)
        result = await session.execute(query)
        return list(result.scalars().all())

    async def count(
        self,
        session: AsyncSession,
        *,
        include_deleted: bool = False,
    ) -> int:
        """
        Count total records.

        Args:
            session: Database session.
            include_deleted: Include soft-deleted records.

        Returns:
            Total count.
        """
        query = select(func.count()).select_from(self.model)

        if hasattr(self.model, "deleted_at") and not include_deleted:
            query = query.where(self.model.deleted_at.is_(None))

        result = await session.execute(query)
        return result.scalar() or 0

    async def create(
        self,
        session: AsyncSession,
        *,
        obj_in: CreateSchemaType,
        process_ai: bool = True,
    ) -> ModelType:
        """
        Create a new record.

        If AI is enabled in settings and process_ai=True, AIFields
        will be automatically populated after creation.

        Signals emitted:
        - PRE_SAVE: Before the record is saved
        - POST_SAVE: After the record is saved (with created=True)

        Args:
            session: Database session.
            obj_in: Creation schema.
            process_ai: Process AI fields (if enabled in settings).

        Returns:
            The created record.
        """
        from p8s.core.settings import get_settings
        from p8s.db.signals import Signal, send_async

        obj_data = obj_in.model_dump()
        db_obj = self.model(**obj_data)

        # Emit PRE_SAVE signal
        await send_async(
            Signal.PRE_SAVE, sender=self.model, instance=db_obj, created=True
        )

        session.add(db_obj)
        await session.flush()
        await session.refresh(db_obj)

        # Process AI fields if enabled
        settings = get_settings()
        if process_ai and settings.ai.enabled and settings.ai.process_on_create:
            try:
                from p8s.ai.processor import process_ai_fields, process_vector_fields

                await process_ai_fields(db_obj)
                await process_vector_fields(db_obj)

                session.add(db_obj)
                await session.flush()
                await session.refresh(db_obj)
            except ImportError:
                pass  # AI module not installed
            except Exception as e:
                import logging

                logging.getLogger("p8s.crud").warning(f"AI processing failed: {e}")

        # Emit POST_SAVE signal
        await send_async(
            Signal.POST_SAVE, sender=self.model, instance=db_obj, created=True
        )

        return db_obj

    async def update(
        self,
        session: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | dict[str, Any],
        process_ai: bool = True,
    ) -> ModelType:
        """
        Update a record.

        If AI is enabled in settings and process_ai=True, AIFields
        will be regenerated when their source fields change.

        Signals emitted:
        - PRE_SAVE: Before the record is saved
        - POST_SAVE: After the record is saved (with created=False)

        Args:
            session: Database session.
            db_obj: Existing record.
            obj_in: Update schema or dict.
            process_ai: Process AI fields (if enabled in settings).

        Returns:
            The updated record.
        """
        from p8s.core.settings import get_settings
        from p8s.db.signals import Signal, send_async

        # Store original values to detect changes
        original_values = db_obj.model_dump()

        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        # Emit PRE_SAVE signal
        await send_async(
            Signal.PRE_SAVE, sender=self.model, instance=db_obj, created=False
        )

        session.add(db_obj)
        await session.flush()
        await session.refresh(db_obj)

        # Process AI fields if enabled and source fields changed
        settings = get_settings()
        if process_ai and settings.ai.enabled and settings.ai.process_on_update:
            try:
                from p8s.ai.processor import (
                    get_ai_field_metadata,
                    process_ai_fields,
                    process_vector_fields,
                    source_fields_changed,
                )

                # Find AI fields whose sources changed
                ai_fields = get_ai_field_metadata(type(db_obj))
                fields_to_process = []

                for field_name, config in ai_fields.items():
                    if source_fields_changed(db_obj, original_values, field_name):
                        fields_to_process.append(field_name)

                if fields_to_process:
                    await process_ai_fields(
                        db_obj, fields=fields_to_process, force=True
                    )
                    await process_vector_fields(db_obj, force=True)

                    session.add(db_obj)
                    await session.flush()
                    await session.refresh(db_obj)

            except ImportError:
                pass  # AI module not installed
            except Exception as e:
                import logging

                logging.getLogger("p8s.crud").warning(f"AI processing failed: {e}")

        # Emit POST_SAVE signal
        await send_async(
            Signal.POST_SAVE, sender=self.model, instance=db_obj, created=False
        )

        return db_obj

    async def delete(
        self,
        session: AsyncSession,
        *,
        id: UUID,
        soft: bool = True,
    ) -> ModelType | None:
        """
        Delete a record.

        Signals emitted:
        - PRE_DELETE: Before the record is deleted
        - POST_DELETE: After the record is deleted

        Args:
            session: Database session.
            id: Record ID.
            soft: Use soft delete if available.

        Returns:
            The deleted record or None.
        """
        from p8s.db.signals import Signal, send_async

        obj = await self.get(session, id)
        if not obj:
            return None

        # Emit PRE_DELETE signal
        await send_async(Signal.PRE_DELETE, sender=self.model, instance=obj)

        if soft and hasattr(obj, "soft_delete"):
            obj.soft_delete()
            session.add(obj)
        else:
            await session.delete(obj)

        await session.flush()

        # Emit POST_DELETE signal
        await send_async(Signal.POST_DELETE, sender=self.model, instance=obj)

        return obj


def generate_crud_routes(
    path: str,
    model: type[SQLModel],
    *,
    create: bool = True,
    read: bool = True,
    update: bool = True,
    delete: bool = True,
    list_route: bool = True,
    response_model: type[BaseModel] | None = None,
    create_schema: type[BaseModel] | None = None,
    update_schema: type[BaseModel] | None = None,
) -> APIRouter:
    """
    Generate CRUD routes for a model.

    Args:
        path: Base path for routes.
        model: The SQLModel class.
        create: Include POST route.
        read: Include GET /{id} route.
        update: Include PATCH /{id} route.
        delete: Include DELETE /{id} route.
        list_route: Include GET / route.
        response_model: Response schema.
        create_schema: Creation schema.
        update_schema: Update schema.

    Returns:
        APIRouter with CRUD routes.
    """
    router = APIRouter()
    crud = CRUDBase(model)

    # Use model as response if not specified
    resp_model = response_model or model

    if list_route:

        @router.get(path, response_model=list[resp_model])
        async def list_items(
            skip: int = Query(0, ge=0),
            limit: int = Query(100, ge=1, le=1000),
            session: AsyncSession = get_session,
        ):
            return await crud.list(session, skip=skip, limit=limit)

    if create and create_schema:

        @router.post(path, response_model=resp_model, status_code=201)
        async def create_item(
            item: create_schema,
            session: AsyncSession = get_session,
        ):
            return await crud.create(session, obj_in=item)

    if read:

        @router.get(f"{path}/{{id}}", response_model=resp_model)
        async def get_item(
            id: UUID,
            session: AsyncSession = get_session,
        ):
            return await crud.get_or_404(session, id)

    if update and update_schema:

        @router.patch(f"{path}/{{id}}", response_model=resp_model)
        async def update_item(
            id: UUID,
            item: update_schema,
            session: AsyncSession = get_session,
        ):
            db_obj = await crud.get_or_404(session, id)
            return await crud.update(session, db_obj=db_obj, obj_in=item)

    if delete:

        @router.delete(f"{path}/{{id}}", response_model=resp_model)
        async def delete_item(
            id: UUID,
            session: AsyncSession = get_session,
        ):
            obj = await crud.delete(session, id=id)
            if not obj:
                raise HTTPException(status_code=404, detail="Not found")
            return obj

    return router
