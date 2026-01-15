"""
P8s Application - The main application factory.

Creates a FastAPI application with all P8s batteries included.
"""

from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from p8s.core.settings import Settings, get_settings


class P8sApp(FastAPI):
    """
    P8s Application class.

    Extends FastAPI with P8s-specific features:
    - Automatic CORS configuration
    - Database initialization
    - Admin panel mounting
    - Static files serving
    - App discovery

    Example:
        ```python
        from p8s import P8sApp

        app = P8sApp(title="My App")
        ```
    """

    def __init__(
        self,
        settings: Settings | None = None,
        title: str | None = None,
        description: str = "",
        version: str = "0.1.0",
        lifespan: Callable[..., AsyncGenerator[None, None]] | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize P8s application.

        Args:
            settings: P8s settings instance. If None, loads from environment.
            title: Application title (overrides settings.app_name).
            description: Application description for OpenAPI.
            version: Application version.
            lifespan: Custom lifespan context manager.
            **kwargs: Additional FastAPI arguments.
        """
        self.p8s_settings = settings or get_settings()

        # Use provided lifespan or create default
        app_lifespan = lifespan or self._default_lifespan

        # Disable default docs - we'll add protected versions
        # Note: We pass debug=False to disable Starlette's default error pages
        # P8s has its own styled debug/error pages that respect p8s_settings.debug
        super().__init__(
            title=title or self.p8s_settings.app_name,
            description=description,
            version=version,
            debug=False,  # Use P8s custom error pages instead of Starlette's
            lifespan=app_lifespan,
            docs_url=None,  # Disable default docs
            redoc_url=None,  # Disable default redoc
            openapi_url=None,  # Disable default openapi.json
            **kwargs,
        )

        self._setup_cors()
        self._setup_exception_handlers()
        self._setup_static_files()
        self._setup_favicon()
        self._setup_protected_docs()

        # Mount admin panel if enabled
        if self.p8s_settings.admin.enabled:
            self._mount_admin()

        # Mount auth router
        self._mount_auth()

        # Discover and register apps
        self._discover_apps()

    @asynccontextmanager
    async def _default_lifespan(self, app: FastAPI) -> AsyncGenerator[None, None]:
        """Default lifespan context manager."""
        # Startup
        await self._on_startup()
        yield
        # Shutdown
        await self._on_shutdown()

    async def _on_startup(self) -> None:
        """Application startup tasks."""
        from p8s.db.session import init_db

        # Initialize database
        await init_db(self.p8s_settings.database)

    async def _on_shutdown(self) -> None:
        """Application shutdown tasks."""
        from p8s.db.session import close_db

        await close_db()

    def _setup_cors(self) -> None:
        """Configure CORS middleware."""
        self.add_middleware(
            CORSMiddleware,
            allow_origins=self.p8s_settings.cors_origins,
            allow_credentials=self.p8s_settings.cors_allow_credentials,
            allow_methods=self.p8s_settings.cors_allow_methods,
            allow_headers=self.p8s_settings.cors_allow_headers,
        )

    def _setup_exception_handlers(self) -> None:
        """
        Setup custom exception handlers.

        In DEBUG mode: Shows detailed Django-style error pages.
        In PRODUCTION mode: Shows generic styled error pages.

        Users can override error templates by creating files in:
        templates/errors/{status_code}.html
        """
        from pathlib import Path

        from fastapi import HTTPException
        from starlette.exceptions import HTTPException as StarletteHTTPException

        from p8s.core.exceptions import (
            create_exception_handlers,
        )

        # Determine templates directory for user overrides
        templates_dir = Path(self.p8s_settings.base_dir) / "templates"

        # Create handlers with current debug setting
        handlers = create_exception_handlers(
            debug=self.p8s_settings.debug,
            templates_dir=templates_dir if templates_dir.exists() else None,
        )

        # Register all handlers
        for exc_type, handler in handlers.items():
            self.add_exception_handler(exc_type, handler)

        # Also register for Starlette's HTTPException (used internally by FastAPI for 404s)
        if HTTPException in handlers:
            self.add_exception_handler(StarletteHTTPException, handlers[HTTPException])

    def _setup_static_files(self) -> None:
        """Mount static files directory."""
        from pathlib import Path

        static_dir = Path(self.p8s_settings.base_dir) / self.p8s_settings.static_dir

        if static_dir.exists():
            self.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

        media_dir = Path(self.p8s_settings.base_dir) / self.p8s_settings.media_dir

        if media_dir.exists():
            self.mount("/media", StaticFiles(directory=str(media_dir)), name="media")

    def _setup_favicon(self) -> None:
        """
        Setup global favicon serving.

        Serves /p8s.svg and /favicon.ico.
        Checks user static dir for overrides first.
        """
        from pathlib import Path

        import p8s.admin

        @self.get("/p8s.svg", include_in_schema=False)
        async def favicon_svg():
            # Check user override
            user_static = (
                Path(self.p8s_settings.base_dir) / self.p8s_settings.static_dir
            )
            if (user_static / "p8s.svg").exists():
                return FileResponse(user_static / "p8s.svg")

            # Default
            admin_path = Path(p8s.admin.__file__).parent

            # Try built static first
            default_icon = admin_path / "static" / "p8s.svg"
            if default_icon.exists():
                return FileResponse(default_icon)

            # Fallback to source in dev
            source_icon = admin_path / "ui" / "public" / "p8s.svg"
            if source_icon.exists():
                return FileResponse(source_icon)

            return HTMLResponse("Not Found", status_code=404)

        @self.get("/favicon.ico", include_in_schema=False)
        async def favicon_ico():
            # Check user override for ico
            user_static = (
                Path(self.p8s_settings.base_dir) / self.p8s_settings.static_dir
            )
            if (user_static / "favicon.ico").exists():
                return FileResponse(user_static / "favicon.ico")

            # Fallback to SVG if only that exists (browsers handle this fine often, or user overrides p8s.svg)
            # Or redirect to p8s.svg? Redirect is better
            return await favicon_svg()

    def _setup_protected_docs(self) -> None:
        """
        Setup OpenAPI docs.

        Docs are only available in debug mode for security:
        - /docs (Swagger UI)
        - /redoc (ReDoc)
        - /openapi.json (OpenAPI schema)

        In production (DEBUG=False), these endpoints return 404.
        """
        from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
        from fastapi.responses import JSONResponse

        # Only enable docs in debug mode
        if not self.p8s_settings.debug:
            return

        @self.get("/openapi.json", include_in_schema=False)
        async def get_openapi_schema():
            """Get OpenAPI schema."""
            return JSONResponse(self.openapi())

        @self.get("/docs", include_in_schema=False)
        async def get_docs():
            """Get Swagger UI docs."""
            return get_swagger_ui_html(
                openapi_url="/openapi.json",
                title=f"{self.title} - Docs",
                swagger_favicon_url="/p8s.svg",
            )

        @self.get("/redoc", include_in_schema=False)
        async def get_redoc():
            """Get ReDoc docs."""
            return get_redoc_html(
                openapi_url="/openapi.json",
                title=f"{self.title} - ReDoc",
            )

    def _mount_admin(self) -> None:
        """Mount the admin panel."""
        from p8s.admin.router import create_admin_router

        admin_router = create_admin_router(self.p8s_settings.admin)
        self.include_router(
            admin_router,
            prefix=self.p8s_settings.admin.path,
            tags=["admin"],
        )

    def _mount_auth(self) -> None:
        """Mount the auth router."""
        from p8s.auth.router import router as auth_router

        self.include_router(auth_router)

    def _discover_apps(self) -> None:
        """
        Discover and register installed apps.

        Apps are registered from settings.installed_apps.
        Each app should have a router.py with a 'router' variable.
        """
        import importlib

        for app_name in self.p8s_settings.installed_apps:
            try:
                # Try to import app.router
                module = importlib.import_module(f"{app_name}.router")

                if hasattr(module, "router"):
                    self.include_router(
                        module.router,
                        prefix=f"/{app_name.split('.')[-1]}",
                        tags=[app_name.split(".")[-1]],
                    )
            except ImportError:
                # App doesn't have a router, skip
                pass

    def register_app(
        self,
        app_name: str,
        prefix: str | None = None,
        tags: list[str] | None = None,
    ) -> None:
        """
        Manually register an app.

        Args:
            app_name: The app module name.
            prefix: URL prefix (default: /{app_name}).
            tags: OpenAPI tags.
        """
        import importlib

        module = importlib.import_module(f"{app_name}.router")

        if hasattr(module, "router"):
            self.include_router(
                module.router,
                prefix=prefix or f"/{app_name.split('.')[-1]}",
                tags=tags or [app_name.split(".")[-1]],
            )

    def add_p8s_middleware(self, middleware: Any, **kwargs: Any) -> None:
        """
        Add a P8s middleware to the application.

        This is a convenience method that automatically wraps P8s middlewares
        with MiddlewareWrapper for compatibility with FastAPI/Starlette.

        Example:
            ```python
            from p8s import P8sApp
            from p8s.middleware import RateLimitMiddleware

            app = P8sApp()
            app.add_p8s_middleware(RateLimitMiddleware, rate="100/minute")
            ```

        Args:
            middleware: P8s Middleware class or instance.
            **kwargs: Arguments to pass to the middleware constructor.
        """
        from p8s.middleware import Middleware, MiddlewareWrapper

        # If it's a class, instantiate it
        if isinstance(middleware, type):
            if issubclass(middleware, Middleware):
                instance = middleware(**kwargs)
                self.add_middleware(MiddlewareWrapper, middleware=instance)
            else:
                # It's a regular Starlette middleware class
                self.add_middleware(middleware, **kwargs)
        elif isinstance(middleware, Middleware):
            # It's already an instance
            self.add_middleware(MiddlewareWrapper, middleware=middleware)
        else:
            raise TypeError(
                f"Expected P8s Middleware class or instance, got {type(middleware)}"
            )
