"""
P8s Settings - Centralized configuration management.

Inspired by Django's settings.py but using Pydantic for validation.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration."""

    model_config = SettingsConfigDict(
        env_prefix="P8S_DB_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database URL (supports async drivers)
    url: str = Field(
        default="sqlite+aiosqlite:///./db.sqlite3",
        description="Database connection URL",
    )

    # Connection pool settings
    pool_size: int = Field(default=5, ge=1, le=100)
    pool_overflow: int = Field(default=10, ge=0, le=100)
    pool_timeout: int = Field(default=30, ge=1)

    # Echo SQL queries (for debugging)
    echo: bool = Field(default=False)


class AuthSettings(BaseSettings):
    """Authentication configuration."""

    model_config = SettingsConfigDict(
        env_prefix="P8S_AUTH_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # JWT settings
    secret_key: str = Field(
        default="p8s-secret-key-change-in-production",
        description="Secret key for JWT encoding",
    )
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30, ge=1)
    refresh_token_expire_days: int = Field(default=7, ge=1)

    # Password hashing
    bcrypt_rounds: int = Field(default=12, ge=4, le=31)


class AISettings(BaseSettings):
    """
    AI/LLM configuration - Django-style optional settings.

    All AI features are disabled by default. Enable by setting:
        P8S_AI_ENABLED=true
        P8S_AI_OPENAI_API_KEY=sk-...

    Supports multiple providers:
        - OpenAI (default)
        - Anthropic (Claude)
        - Google (Gemini)
        - Azure OpenAI
        - Ollama (local)
        - Custom endpoints
    """

    model_config = SettingsConfigDict(
        env_prefix="P8S_AI_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # =========================================================================
    # Core settings - MUST be enabled to use AI features
    # =========================================================================

    enabled: bool = Field(
        default=False,
        description="Enable AI field processing. Set to true to activate AI features.",
    )

    # =========================================================================
    # Provider configuration
    # =========================================================================

    provider: Literal["openai", "anthropic", "gemini", "azure", "ollama", "custom"] = (
        Field(default="openai", description="LLM provider to use")
    )

    # Default model for text generation (overridable per-field)
    model: str = Field(
        default="gpt-4o-mini", description="Default model for text generation"
    )

    # =========================================================================
    # API Keys - loaded from environment variables
    # =========================================================================

    # OpenAI
    openai_api_key: str | None = Field(
        default=None, description="OpenAI API key (P8S_AI_OPENAI_API_KEY)"
    )
    openai_organization: str | None = Field(
        default=None, description="OpenAI organization ID"
    )
    openai_base_url: str | None = Field(
        default=None, description="Custom OpenAI base URL (for proxies)"
    )

    # Anthropic
    anthropic_api_key: str | None = Field(default=None, description="Anthropic API key")

    # Google Gemini
    gemini_api_key: str | None = Field(
        default=None, description="Google Gemini API key"
    )

    # Azure OpenAI
    azure_api_key: str | None = Field(default=None, description="Azure OpenAI API key")
    azure_endpoint: str | None = Field(
        default=None, description="Azure OpenAI endpoint URL"
    )
    azure_api_version: str = Field(
        default="2024-02-15-preview", description="Azure OpenAI API version"
    )
    azure_deployment: str | None = Field(
        default=None, description="Azure deployment name"
    )

    # Ollama (local)
    ollama_base_url: str = Field(
        default="http://localhost:11434", description="Ollama server URL"
    )

    # Custom provider
    custom_base_url: str | None = Field(
        default=None, description="Custom LLM endpoint URL"
    )
    custom_api_key: str | None = Field(default=None, description="Custom LLM API key")

    # =========================================================================
    # Generation settings - defaults, overridable per-field
    # =========================================================================

    temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="Default temperature for generation"
    )
    max_tokens: int = Field(
        default=1000, ge=1, le=100000, description="Default max tokens for generation"
    )
    timeout: int = Field(default=60, ge=1, description="Request timeout in seconds")

    # =========================================================================
    # Embeddings configuration
    # =========================================================================

    embedding_enabled: bool = Field(
        default=False, description="Enable vector embeddings for VectorField"
    )
    embedding_provider: Literal["openai", "ollama", "custom"] = Field(
        default="openai", description="Provider for embeddings"
    )
    embedding_model: str = Field(
        default="text-embedding-3-small", description="Model for generating embeddings"
    )
    embedding_dimensions: int = Field(
        default=1536, ge=1, le=4096, description="Embedding vector dimensions"
    )

    # =========================================================================
    # Caching - reduce API costs
    # =========================================================================

    cache_enabled: bool = Field(default=True, description="Cache AI responses")
    cache_ttl: int = Field(
        default=3600, ge=0, description="Cache TTL in seconds (0 = forever)"
    )

    # =========================================================================
    # Processing behavior
    # =========================================================================

    process_on_create: bool = Field(
        default=True, description="Process AI fields when model is created"
    )
    process_on_update: bool = Field(
        default=True, description="Process AI fields when source fields change"
    )
    async_processing: bool = Field(
        default=False, description="Process AI fields asynchronously (background task)"
    )
    retry_on_error: bool = Field(
        default=True, description="Retry failed AI generations"
    )
    max_retries: int = Field(
        default=3, ge=0, le=10, description="Maximum number of retries"
    )

    def is_configured(self) -> bool:
        """Check if AI is properly configured to work."""
        if not self.enabled:
            return False

        # Check if required API key is present for provider
        provider_keys = {
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
            "gemini": self.gemini_api_key,
            "azure": self.azure_api_key,
            "custom": self.custom_api_key,
            "ollama": True,  # Ollama doesn't need API key
        }

        return bool(provider_keys.get(self.provider))

    def get_api_key(self) -> str | None:
        """Get the API key for the current provider."""
        return {
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
            "gemini": self.gemini_api_key,
            "azure": self.azure_api_key,
            "custom": self.custom_api_key,
            "ollama": None,
        }.get(self.provider)


class FrontendSettings(BaseSettings):
    """Frontend (React) configuration."""

    model_config = SettingsConfigDict(
        env_prefix="P8S_FRONTEND_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Paths
    build_dir: str = Field(default="frontend/dist")
    src_dir: str = Field(default="frontend/src")

    # Development server
    dev_port: int = Field(default=5173, ge=1024, le=65535)

    # Type generation
    types_output_dir: str = Field(default="frontend/src/types")
    auto_generate_types: bool = Field(default=True)


class AdminSettings(BaseSettings):
    """Admin panel configuration."""

    model_config = SettingsConfigDict(
        env_prefix="P8S_ADMIN_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Admin panel settings
    enabled: bool = Field(default=True)
    path: str = Field(default="/admin")
    title: str = Field(default="P8s Admin")

    # Pagination
    items_per_page: int = Field(default=25, ge=1, le=1000)


class Settings(BaseSettings):
    """
    Main P8s settings class.

    All settings can be overridden via environment variables prefixed with P8S_.

    Example:
        P8S_DEBUG=true
        P8S_DB_URL=postgresql+asyncpg://user:pass@localhost/db
        P8S_AI_PROVIDER=anthropic
    """

    model_config = SettingsConfigDict(
        env_prefix="P8S_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="P8s App")
    debug: bool = Field(default=False)
    secret_key: str = Field(default="p8s-secret-key-change-me")

    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, ge=1024, le=65535)
    reload: bool = Field(default=True)

    # CORS
    cors_origins: list[str] = Field(default=["http://localhost:5173"])
    cors_allow_credentials: bool = Field(default=True)
    cors_allow_methods: list[str] = Field(default=["*"])
    cors_allow_headers: list[str] = Field(default=["*"])

    # Paths
    base_dir: Path = Field(default_factory=Path.cwd)
    apps_dir: str = Field(default="backend/apps")
    static_dir: str = Field(default="static")
    media_dir: str = Field(default="media")

    # Installed apps (Django-style)
    installed_apps: list[str] = Field(default=[])

    # Middleware
    middleware: list[str] = Field(default=[])

    # Nested settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    ai: AISettings = Field(default_factory=AISettings)
    frontend: FrontendSettings = Field(default_factory=FrontendSettings)
    admin: AdminSettings = Field(default_factory=AdminSettings)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("installed_apps", mode="before")
    @classmethod
    def parse_installed_apps(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return [app.strip() for app in v.split(",") if app.strip()]
        return v


def _discover_settings_class() -> type[Settings]:
    """
    Discover the settings class from P8S_SETTINGS_MODULE.

    Like Django's DJANGO_SETTINGS_MODULE, this allows projects to define
    their own settings by subclassing Settings.

    Environment variable: P8S_SETTINGS_MODULE
    Example: P8S_SETTINGS_MODULE=backend.settings.AppSettings

    If only module path is given (e.g., "backend.settings"), looks for
    AppSettings or Settings class in that module.
    """
    import importlib
    import os

    settings_module = os.environ.get("P8S_SETTINGS_MODULE")

    if not settings_module:
        return Settings

    try:
        # Split module path and class name
        if "." in settings_module:
            # Try as module.ClassName first
            parts = settings_module.rsplit(".", 1)
            module_path, maybe_class = parts

            try:
                module = importlib.import_module(module_path)
                if hasattr(module, maybe_class):
                    settings_class = getattr(module, maybe_class)
                    if isinstance(settings_class, type) and issubclass(
                        settings_class, Settings
                    ):
                        return settings_class
            except ImportError:
                pass

            # Try as full module path
            try:
                module = importlib.import_module(settings_module)
                for name in ["AppSettings", "Settings"]:
                    if hasattr(module, name):
                        settings_class = getattr(module, name)
                        if isinstance(settings_class, type) and issubclass(
                            settings_class, Settings
                        ):
                            return settings_class
            except ImportError:
                pass

        # Just a module path, look for Settings or AppSettings class
        module = importlib.import_module(settings_module)
        for name in ["AppSettings", "Settings"]:
            if hasattr(module, name):
                settings_class = getattr(module, name)
                if isinstance(settings_class, type) and issubclass(
                    settings_class, Settings
                ):
                    return settings_class
        return Settings
    except (ImportError, AttributeError) as e:
        import warnings

        warnings.warn(f"Could not load settings from {settings_module}: {e}")
        return Settings


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Looks for P8S_SETTINGS_MODULE environment variable to load
    project-specific settings. Falls back to default Settings.

    Example:
        P8S_SETTINGS_MODULE=backend.settings  # Will look for AppSettings or Settings class
        P8S_SETTINGS_MODULE=backend.settings.AppSettings  # Explicit class

    Returns:
        Settings: The application settings.
    """
    settings_class = _discover_settings_class()
    return settings_class()
