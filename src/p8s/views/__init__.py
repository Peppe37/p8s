"""
P8s Class-Based Views - Django-style generic views.

Provides reusable view classes for common CRUD patterns:
- View: Base view class
- ListView: Display a list of objects
- DetailView: Display a single object
- CreateView: Create a new object
- UpdateView: Update an existing object
- DeleteView: Delete an object

Example:
    ```python
    from p8s.views import ListView, DetailView, CreateView

    class ProductListView(ListView):
        model = Product
        paginate_by = 20

    class ProductDetailView(DetailView):
        model = Product

    class ProductCreateView(CreateView):
        model = Product
        fields = ["name", "price", "category"]
    ```
"""

from abc import ABC
from typing import TYPE_CHECKING, Any, Generic, TypeVar
from uuid import UUID

from fastapi import Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from p8s.db.session import get_session

if TYPE_CHECKING:
    from sqlmodel import SQLModel

T = TypeVar("T", bound="SQLModel")


class View:
    """
    Base class for all views.

    Provides common functionality like request handling
    and response formatting.
    """

    async def dispatch(self, request: Request, **kwargs: Any) -> Any:
        """
        Dispatch request to appropriate handler method.

        Args:
            request: FastAPI request
            **kwargs: Additional arguments

        Returns:
            Response from handler
        """
        method = request.method.lower()
        handler = getattr(self, method, None)

        if handler is None:
            raise HTTPException(
                status_code=405, detail=f"Method {request.method} not allowed"
            )

        return await handler(request, **kwargs)


class ListView(Generic[T]):
    """
    View for displaying a list of objects with pagination.

    Attributes:
        model: SQLModel class to query
        paginate_by: Number of items per page (default: 25)
        ordering: Default ordering field (prefix with - for desc)

    Example:
        ```python
        class ProductListView(ListView):
            model = Product
            paginate_by = 20
            ordering = "-created_at"
        ```
    """

    model: type[T] | None = None
    paginate_by: int = 25
    ordering: str | None = None

    def get_queryset(self):
        """Get base query for the model."""
        if self.model is None:
            raise ValueError("ListView requires a model attribute")
        return select(self.model)

    async def get(
        self,
        request: Request,
        page: int = Query(1, ge=1),
        page_size: int | None = None,
        session: AsyncSession = Depends(get_session),
    ) -> dict[str, Any]:
        """
        Handle GET request for list view.

        Args:
            request: FastAPI request
            page: Page number
            page_size: Items per page (uses paginate_by if not specified)
            session: Database session

        Returns:
            Paginated list of items
        """
        if self.model is None:
            raise ValueError("ListView requires a model attribute")

        per_page = page_size or self.paginate_by
        skip = (page - 1) * per_page

        query = self.get_queryset()

        # Apply ordering
        if self.ordering:
            desc = self.ordering.startswith("-")
            field_name = self.ordering.lstrip("-")
            if hasattr(self.model, field_name):
                field = getattr(self.model, field_name)
                query = query.order_by(field.desc() if desc else field.asc())

        # Get total count
        count_query = select(func.count()).select_from(self.model)
        count_result = await session.execute(count_query)
        total = count_result.scalar() or 0

        # Apply pagination
        query = query.offset(skip).limit(per_page)

        # Execute query
        result = await session.execute(query)
        items = result.scalars().all()

        return {
            "items": [item.model_dump() for item in items],
            "total": total,
            "page": page,
            "page_size": per_page,
            "pages": (total + per_page - 1) // per_page,
        }


class DetailView(Generic[T]):
    """
    View for displaying a single object.

    Attributes:
        model: SQLModel class to query
        pk_field: Primary key field name (default: "id")

    Example:
        ```python
        class ProductDetailView(DetailView):
            model = Product
        ```
    """

    model: type[T] | None = None
    pk_field: str = "id"

    async def get_object(
        self,
        pk: UUID | int | str,
        session: AsyncSession,
    ) -> T:
        """
        Get the object by primary key.

        Args:
            pk: Primary key value
            session: Database session

        Returns:
            The requested object

        Raises:
            HTTPException: If object not found
        """
        if self.model is None:
            raise ValueError("DetailView requires a model attribute")

        pk_column = getattr(self.model, self.pk_field)
        query = select(self.model).where(pk_column == pk)

        result = await session.execute(query)
        obj = result.scalar_one_or_none()

        if obj is None:
            raise HTTPException(status_code=404, detail="Object not found")

        return obj

    async def get(
        self,
        request: Request,
        pk: UUID,
        session: AsyncSession = Depends(get_session),
    ) -> dict[str, Any]:
        """
        Handle GET request for detail view.

        Args:
            request: FastAPI request
            pk: Primary key of the object
            session: Database session

        Returns:
            Object data
        """
        obj = await self.get_object(pk, session)
        return obj.model_dump()


class CreateView(Generic[T]):
    """
    View for creating a new object.

    Attributes:
        model: SQLModel class to create
        fields: List of fields allowed in creation

    Example:
        ```python
        class ProductCreateView(CreateView):
            model = Product
            fields = ["name", "price", "category_id"]
        ```
    """

    model: type[T] | None = None
    fields: list[str] | None = None

    async def post(
        self,
        request: Request,
        session: AsyncSession = Depends(get_session),
    ) -> dict[str, Any]:
        """
        Handle POST request to create object.

        Args:
            request: FastAPI request with JSON body
            session: Database session

        Returns:
            Created object data
        """
        if self.model is None:
            raise ValueError("CreateView requires a model attribute")

        data = await request.json()

        # Filter to allowed fields
        if self.fields:
            data = {k: v for k, v in data.items() if k in self.fields}

        try:
            obj = self.model(**data)
            session.add(obj)
            await session.flush()
            await session.refresh(obj)

            return obj.model_dump()
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))


class UpdateView(Generic[T]):
    """
    View for updating an existing object.

    Attributes:
        model: SQLModel class to update
        fields: List of fields allowed in update
        pk_field: Primary key field name (default: "id")

    Example:
        ```python
        class ProductUpdateView(UpdateView):
            model = Product
            fields = ["name", "price"]
        ```
    """

    model: type[T] | None = None
    fields: list[str] | None = None
    pk_field: str = "id"

    async def get_object(
        self,
        pk: UUID | int | str,
        session: AsyncSession,
    ) -> T:
        """Get the object by primary key."""
        if self.model is None:
            raise ValueError("UpdateView requires a model attribute")

        pk_column = getattr(self.model, self.pk_field)
        query = select(self.model).where(pk_column == pk)

        result = await session.execute(query)
        obj = result.scalar_one_or_none()

        if obj is None:
            raise HTTPException(status_code=404, detail="Object not found")

        return obj

    async def put(
        self,
        request: Request,
        pk: UUID,
        session: AsyncSession = Depends(get_session),
    ) -> dict[str, Any]:
        """
        Handle PUT request to update object.

        Args:
            request: FastAPI request with JSON body
            pk: Primary key of the object
            session: Database session

        Returns:
            Updated object data
        """
        obj = await self.get_object(pk, session)
        data = await request.json()

        # Filter to allowed fields
        if self.fields:
            data = {k: v for k, v in data.items() if k in self.fields}

        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)

        session.add(obj)
        await session.flush()
        await session.refresh(obj)

        return obj.model_dump()

    async def patch(
        self,
        request: Request,
        pk: UUID,
        session: AsyncSession = Depends(get_session),
    ) -> dict[str, Any]:
        """Handle PATCH request (same as PUT for partial updates)."""
        return await self.put(request, pk, session)


class DeleteView(Generic[T]):
    """
    View for deleting an object.

    Attributes:
        model: SQLModel class to delete
        pk_field: Primary key field name (default: "id")
        soft_delete: Use soft delete if available (default: True)

    Example:
        ```python
        class ProductDeleteView(DeleteView):
            model = Product
        ```
    """

    model: type[T] | None = None
    pk_field: str = "id"
    soft_delete: bool = True

    async def get_object(
        self,
        pk: UUID | int | str,
        session: AsyncSession,
    ) -> T:
        """Get the object by primary key."""
        if self.model is None:
            raise ValueError("DeleteView requires a model attribute")

        pk_column = getattr(self.model, self.pk_field)
        query = select(self.model).where(pk_column == pk)

        result = await session.execute(query)
        obj = result.scalar_one_or_none()

        if obj is None:
            raise HTTPException(status_code=404, detail="Object not found")

        return obj

    async def delete(
        self,
        request: Request,
        pk: UUID,
        session: AsyncSession = Depends(get_session),
    ) -> dict[str, str]:
        """
        Handle DELETE request.

        Args:
            request: FastAPI request
            pk: Primary key of the object
            session: Database session

        Returns:
            Success message
        """
        obj = await self.get_object(pk, session)

        if self.soft_delete and hasattr(obj, "soft_delete"):
            obj.soft_delete()
            session.add(obj)
        else:
            await session.delete(obj)

        await session.flush()

        return {"detail": "Object deleted"}


# Helper to convert view class to FastAPI route
def as_route(view_class: type):
    """
    Convert a class-based view to a FastAPI route handler.

    Example:
        ```python
        from p8s.views import ListView, as_route

        class ProductListView(ListView):
            model = Product

        app.get("/products/")(as_route(ProductListView))
        ```
    """
    view = view_class()

    async def route_handler(request: Request, **kwargs):
        return await view.dispatch(request, **kwargs)

    return route_handler


__all__ = [
    "View",
    "ListView",
    "DetailView",
    "CreateView",
    "UpdateView",
    "DeleteView",
    "as_route",
]
