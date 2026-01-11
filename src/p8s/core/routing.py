"""
P8s Router - Enhanced routing utilities.
"""

from collections.abc import Callable
from typing import Any, TypeVar

from fastapi import APIRouter

T = TypeVar("T")


class Router(APIRouter):
    """
    Enhanced P8s Router.

    Extends FastAPI's APIRouter with convenience methods.

    Example:
        ```python
        from p8s.core import Router

        router = Router(prefix="/api")

        @router.get("/items")
        async def list_items():
            return []
        ```
    """

    def __init__(
        self,
        prefix: str = "",
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(prefix=prefix, tags=tags or [], **kwargs)

    def crud(
        self,
        path: str,
        model: type[Any],
        *,
        create: bool = True,
        read: bool = True,
        update: bool = True,
        delete: bool = True,
        list_route: bool = True,
    ) -> Callable[[type[T]], type[T]]:
        """
        Decorator to generate CRUD routes for a model.

        Args:
            path: Base path for CRUD routes.
            model: The SQLModel class.
            create: Include POST route.
            read: Include GET /{id} route.
            update: Include PATCH /{id} route.
            delete: Include DELETE /{id} route.
            list_route: Include GET / route.

        Example:
            ```python
            @router.crud("/products", Product)
            class ProductController:
                pass
            ```
        """

        def decorator(cls: type[T]) -> type[T]:
            from p8s.db.crud import generate_crud_routes

            crud_router = generate_crud_routes(
                path=path,
                model=model,
                create=create,
                read=read,
                update=update,
                delete=delete,
                list_route=list_route,
            )
            self.include_router(crud_router)
            return cls

        return decorator

    def api(
        self,
        prefix: str = "/api/v1",
        **kwargs: Any,
    ) -> "Router":
        """
        Create an API sub-router with versioning.

        Args:
            prefix: API prefix (default: /api/v1).
            **kwargs: Additional router arguments.

        Returns:
            A new Router instance.
        """
        sub_router = Router(prefix=prefix, **kwargs)
        self.include_router(sub_router)
        return sub_router
