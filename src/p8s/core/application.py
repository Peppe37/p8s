"""
P8s Application - The main application factory.

Creates a FastAPI application with all P8s batteries included.
"""

from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
        super().__init__(
            title=title or self.p8s_settings.app_name,
            description=description,
            version=version,
            debug=self.p8s_settings.debug,
            lifespan=app_lifespan,
            docs_url=None,  # Disable default docs
            redoc_url=None,  # Disable default redoc
            openapi_url=None,  # Disable default openapi.json
            **kwargs,
        )
        
        self._setup_cors()
        self._setup_exception_handlers()
        self._setup_static_files()
        self._setup_protected_docs()  # Add protected docs
        
        # Mount admin panel if enabled
        if self.p8s_settings.admin.enabled:
            self._mount_admin()
        
        # Mount auth router
        self._mount_auth()
            
        # Discover and register apps
        self._discover_apps()
    
    @asynccontextmanager
    async def _default_lifespan(
        self, app: FastAPI
    ) -> AsyncGenerator[None, None]:
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
        """Setup custom exception handlers."""
        from p8s.core.exceptions import (
            P8sException,
            p8s_exception_handler,
        )
        
        self.add_exception_handler(P8sException, p8s_exception_handler)
    
    def _setup_static_files(self) -> None:
        """Mount static files directory."""
        from pathlib import Path
        
        static_dir = Path(self.p8s_settings.base_dir) / self.p8s_settings.static_dir
        
        if static_dir.exists():
            self.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        
        media_dir = Path(self.p8s_settings.base_dir) / self.p8s_settings.media_dir
        
        if media_dir.exists():
            self.mount("/media", StaticFiles(directory=str(media_dir)), name="media")
    
    def _setup_protected_docs(self) -> None:
        """
        Setup OpenAPI docs protected by admin authentication.
        
        Only authenticated admin users can access:
        - /docs (Swagger UI)
        - /redoc (ReDoc)
        - /openapi.json (OpenAPI schema)
        """
        from fastapi import Depends
        from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
        from fastapi.responses import JSONResponse
        from p8s.auth.dependencies import require_admin
        from p8s.auth.models import User
        
        # Store openapi schema
        @self.get("/openapi.json", include_in_schema=False)
        async def get_openapi_schema(user: User = Depends(require_admin)):
            """Get OpenAPI schema (admin only)."""
            return JSONResponse(self.openapi())
        
        @self.get("/docs", include_in_schema=False)
        async def get_docs(user: User = Depends(require_admin)):
            """Get Swagger UI docs (admin only)."""
            return get_swagger_ui_html(
                openapi_url="/openapi.json",
                title=f"{self.title} - Docs",
            )
        
        @self.get("/redoc", include_in_schema=False)
        async def get_redoc(user: User = Depends(require_admin)):
            """Get ReDoc docs (admin only)."""
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
                        tags=[app_name.split('.')[-1]],
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
                tags=tags or [app_name.split('.')[-1]],
            )
