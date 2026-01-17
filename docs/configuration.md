# Configuration

P8s uses environment variables and Python settings classes for configuration.

## Environment Variables

Create a `.env` file in your project root:

```env
# =============================================================================
# CORE SETTINGS
# =============================================================================

# Application
APP_NAME=MyApp
DEBUG=true

# =============================================================================
# DATABASE
# =============================================================================

# SQLite (development)
DATABASE_URL=sqlite+aiosqlite:///p8s.db

# PostgreSQL (production)
# DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname

# Connection pool
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10

# =============================================================================
# AUTHENTICATION
# =============================================================================

# Required: Generate with `openssl rand -hex 32`
SECRET_KEY=your-256-bit-secret-key-here

# Token expiration
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# =============================================================================
# AI SETTINGS
# =============================================================================

# Enable AI features
P8S_AI_ENABLED=true

# Provider: openai, anthropic, gemini, ollama
P8S_AI_PROVIDER=openai

# OpenAI
P8S_AI_OPENAI_API_KEY=sk-...
P8S_AI_OPENAI_MODEL=gpt-4

# Anthropic
# P8S_AI_ANTHROPIC_API_KEY=sk-ant-...
# P8S_AI_ANTHROPIC_MODEL=claude-3-sonnet

# Ollama (local)
# P8S_AI_OLLAMA_BASE_URL=http://localhost:11434
# P8S_AI_OLLAMA_MODEL=llama2

# Embeddings
P8S_AI_EMBEDDING_ENABLED=true
P8S_AI_EMBEDDING_PROVIDER=openai
P8S_AI_EMBEDDING_MODEL=text-embedding-3-small

# =============================================================================
# CORS (Cross-Origin Resource Sharing)
# =============================================================================

CORS_ORIGINS=http://localhost:5173,http://localhost:8000
CORS_ALLOW_CREDENTIALS=true

# =============================================================================
# ADMIN PANEL
# =============================================================================

ADMIN_ENABLED=true
ADMIN_PATH=/admin
ADMIN_TITLE=P8s Admin
```

## Settings Class

Override settings in `backend/settings.py`:

```python
from p8s.core.settings import Settings, AdminSettings, AISettings

class AppSettings(Settings):
    """Custom application settings."""

    # Override app name
    app_name: str = "My Awesome App"

    # Debug mode
    debug: bool = True

    # Installed apps (Django-style)
    installed_apps: list[str] = [
        "backend.apps.products",
        "backend.apps.orders",
    ]

    # CORS origins
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:8000",
    ]

    # Admin configuration
    admin: AdminSettings = AdminSettings(
        enabled=True,
        path="/admin",
        title="My App Admin",
    )

    # AI configuration
    ai: AISettings = AISettings(
        enabled=True,
        provider="openai",
    )
```

## Settings Discovery

P8s uses `P8S_SETTINGS_MODULE` (like Django's `DJANGO_SETTINGS_MODULE`):

```bash
# Set manually
export P8S_SETTINGS_MODULE=backend.settings

# Or let CLI auto-discover
p8s dev  # Automatically finds backend/settings.py
```

## Available Settings

### Core Settings

| Setting          | Type        | Default     | Description      |
| ---------------- | ----------- | ----------- | ---------------- |
| `app_name`       | `str`       | `"P8s App"` | Application name |
| `debug`          | `bool`      | `False`     | Debug mode       |
| `base_dir`       | `str`       | `"."`       | Base directory   |
| `secret_key`     | `str`       | Required    | JWT secret       |
| `installed_apps` | `list[str]` | `[]`        | Registered apps  |

### Database Settings

| Setting        | Type   | Default | Description              |
| -------------- | ------ | ------- | ------------------------ |
| `url`          | `str`  | SQLite  | Connection string        |
| `pool_size`    | `int`  | `5`     | Connection pool size     |
| `max_overflow` | `int`  | `10`    | Max overflow connections |
| `echo`         | `bool` | `False` | Log SQL queries          |

### Auth Settings

| Setting                       | Type  | Default   | Description       |
| ----------------------------- | ----- | --------- | ----------------- |
| `secret_key`                  | `str` | Required  | JWT signing key   |
| `algorithm`                   | `str` | `"HS256"` | JWT algorithm     |
| `access_token_expire_minutes` | `int` | `30`      | Access token TTL  |
| `refresh_token_expire_days`   | `int` | `7`       | Refresh token TTL |

### Admin Settings

| Setting   | Type   | Default       | Description        |
| --------- | ------ | ------------- | ------------------ |
| `enabled` | `bool` | `True`        | Enable admin panel |
| `path`    | `str`  | `"/admin"`    | Admin URL path     |
| `title`   | `str`  | `"P8s Admin"` | Admin panel title  |

### AI Settings

| Setting             | Type   | Default                    | Description        |
| ------------------- | ------ | -------------------------- | ------------------ |
| `enabled`           | `bool` | `False`                    | Enable AI features |
| `provider`          | `str`  | `"openai"`                 | AI provider        |
| `openai_api_key`    | `str`  | `None`                     | OpenAI API key     |
| `openai_model`      | `str`  | `"gpt-4"`                  | OpenAI model       |
| `embedding_enabled` | `bool` | `False`                    | Enable embeddings  |
| `embedding_model`   | `str`  | `"text-embedding-3-small"` | Embedding model    |

## Accessing Settings

```python
from p8s.core.settings import get_settings

settings = get_settings()

print(settings.app_name)
print(settings.database.url)
print(settings.ai.enabled)
```

## Environment-Specific Settings

Use different `.env` files:

```bash
# Development
cp .env.example .env.development

# Production
cp .env.example .env.production
```

Load specific environment:

```bash
# Using dotenv
export $(cat .env.production | xargs)
p8s dev
```
