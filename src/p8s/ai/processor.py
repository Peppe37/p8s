"""
P8s AI Processor - Handles AIField and VectorField processing.

All processing is opt-in and fully configurable via settings.
No AI operations happen unless explicitly enabled.
"""

import hashlib
import logging
from typing import TYPE_CHECKING, Any

from p8s.core.settings import get_settings

if TYPE_CHECKING:
    from sqlmodel import SQLModel

logger = logging.getLogger("p8s.ai")

# In-memory cache (replace with Redis in production)
_ai_cache: dict[str, tuple[str, float]] = {}


def get_ai_field_metadata(model: type["SQLModel"]) -> dict[str, dict[str, Any]]:
    """
    Extract AIField metadata from a model.

    Args:
        model: SQLModel class to inspect.

    Returns:
        Dict mapping field names to their AI configuration.
    """
    ai_fields = {}

    for field_name, field_info in model.model_fields.items():
        extra = field_info.json_schema_extra or {}

        if extra.get("x-p8s-ai-field"):
            ai_fields[field_name] = {
                "prompt": extra.get("x-p8s-ai-prompt", ""),
                "source_fields": extra.get("x-p8s-ai-source-fields", []),
                "model": extra.get("x-p8s-ai-model"),
                "provider": extra.get("x-p8s-ai-provider"),
                "temperature": extra.get("x-p8s-ai-temperature"),
                "max_tokens": extra.get("x-p8s-ai-max-tokens"),
                "cache": extra.get("x-p8s-ai-cache", True),
            }

    return ai_fields


def get_vector_field_metadata(model: type["SQLModel"]) -> dict[str, dict[str, Any]]:
    """
    Extract VectorField metadata from a model.

    Args:
        model: SQLModel class to inspect.

    Returns:
        Dict mapping field names to their vector configuration.
    """
    vector_fields = {}

    for field_name, field_info in model.model_fields.items():
        extra = field_info.json_schema_extra or {}

        if extra.get("x-p8s-vector-field"):
            vector_fields[field_name] = {
                "source_field": extra.get("x-p8s-vector-source", ""),
                "model": extra.get("x-p8s-vector-model"),
                "dimensions": extra.get("x-p8s-vector-dimensions"),
            }

    return vector_fields


def _cache_key(prompt: str, model: str, provider: str) -> str:
    """Generate cache key for AI response."""
    content = f"{provider}:{model}:{prompt}"
    return hashlib.sha256(content.encode()).hexdigest()


def _get_cached(key: str) -> str | None:
    """Get cached AI response."""
    import time

    settings = get_settings()

    if not settings.ai.cache_enabled:
        return None

    if key in _ai_cache:
        value, timestamp = _ai_cache[key]
        if (
            settings.ai.cache_ttl == 0
            or (time.time() - timestamp) < settings.ai.cache_ttl
        ):
            return value
        else:
            del _ai_cache[key]

    return None


def _set_cached(key: str, value: str) -> None:
    """Set cached AI response."""
    import time

    settings = get_settings()

    if settings.ai.cache_enabled:
        _ai_cache[key] = (value, time.time())


async def generate_ai_content(
    prompt: str,
    *,
    model: str | None = None,
    provider: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    use_cache: bool = True,
) -> str | None:
    """
    Generate AI content using configured provider.

    All parameters default to settings if not specified.
    Returns None if AI is not configured.

    Args:
        prompt: The prompt to send to the LLM.
        model: Override model (defaults to settings.ai.model).
        provider: Override provider (defaults to settings.ai.provider).
        temperature: Override temperature.
        max_tokens: Override max tokens.
        use_cache: Whether to use caching.

    Returns:
        Generated text or None if AI not configured.
    """
    settings = get_settings()

    # Check if AI is enabled and configured
    if not settings.ai.is_configured():
        logger.debug("AI not configured, skipping generation")
        return None

    # Use settings defaults
    provider = provider or settings.ai.provider
    model = model or settings.ai.model
    temperature = temperature if temperature is not None else settings.ai.temperature
    max_tokens = max_tokens or settings.ai.max_tokens

    # Check cache
    if use_cache:
        cache_key = _cache_key(prompt, model, provider)
        cached = _get_cached(cache_key)
        if cached:
            logger.debug("Cache hit for AI generation")
            return cached

    # Get API key
    api_key = settings.ai.get_api_key()

    try:
        # Provider-specific generation
        if provider == "openai":
            result = await _generate_openai(
                prompt, model, api_key, temperature, max_tokens, settings
            )
        elif provider == "anthropic":
            result = await _generate_anthropic(
                prompt, model, api_key, temperature, max_tokens
            )
        elif provider == "gemini":
            result = await _generate_gemini(
                prompt, model, api_key, temperature, max_tokens
            )
        elif provider == "ollama":
            result = await _generate_ollama(
                prompt, model, temperature, max_tokens, settings
            )
        elif provider == "azure":
            result = await _generate_azure(
                prompt, model, api_key, temperature, max_tokens, settings
            )
        elif provider == "custom":
            result = await _generate_custom(
                prompt, model, api_key, temperature, max_tokens, settings
            )
        else:
            logger.error(f"Unknown AI provider: {provider}")
            return None

        # Cache result
        if use_cache and result:
            _set_cached(cache_key, result)

        return result

    except Exception as e:
        logger.error(f"AI generation failed: {e}")
        if settings.ai.retry_on_error:
            # Could implement retry logic here
            pass
        return None


async def _generate_openai(
    prompt: str,
    model: str,
    api_key: str | None,
    temperature: float,
    max_tokens: int,
    settings: Any,
) -> str | None:
    """Generate using OpenAI API."""
    try:
        import httpx

        base_url = settings.ai.openai_base_url or "https://api.openai.com/v1"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        if settings.ai.openai_organization:
            headers["OpenAI-Organization"] = settings.ai.openai_organization

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=settings.ai.timeout) as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    except ImportError:
        logger.error("httpx not installed for OpenAI integration")
        return None
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return None


async def _generate_anthropic(
    prompt: str,
    model: str,
    api_key: str | None,
    temperature: float,
    max_tokens: int,
) -> str | None:
    """Generate using Anthropic API."""
    try:
        import httpx

        headers = {
            "x-api-key": api_key or "",
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]

    except Exception as e:
        logger.error(f"Anthropic API error: {e}")
        return None


async def _generate_gemini(
    prompt: str,
    model: str,
    api_key: str | None,
    temperature: float,
    max_tokens: int,
) -> str | None:
    """Generate using Google Gemini API."""
    try:
        import httpx

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                url,
                params={"key": api_key},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return None


async def _generate_ollama(
    prompt: str,
    model: str,
    temperature: float,
    max_tokens: int,
    settings: Any,
) -> str | None:
    """Generate using local Ollama."""
    try:
        import httpx

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{settings.ai.ollama_base_url}/api/generate",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["response"]

    except Exception as e:
        logger.error(f"Ollama API error: {e}")
        return None


async def _generate_azure(
    prompt: str,
    model: str,
    api_key: str | None,
    temperature: float,
    max_tokens: int,
    settings: Any,
) -> str | None:
    """Generate using Azure OpenAI."""
    try:
        import httpx

        deployment = settings.ai.azure_deployment or model
        url = f"{settings.ai.azure_endpoint}/openai/deployments/{deployment}/chat/completions"

        headers = {
            "api-key": api_key or "",
            "Content-Type": "application/json",
        }

        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                url,
                params={"api-version": settings.ai.azure_api_version},
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    except Exception as e:
        logger.error(f"Azure OpenAI API error: {e}")
        return None


async def _generate_custom(
    prompt: str,
    model: str,
    api_key: str | None,
    temperature: float,
    max_tokens: int,
    settings: Any,
) -> str | None:
    """Generate using custom endpoint (OpenAI-compatible)."""
    try:
        import httpx

        headers = {
            "Authorization": f"Bearer {api_key}" if api_key else "",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{settings.ai.custom_base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    except Exception as e:
        logger.error(f"Custom API error: {e}")
        return None


async def generate_embedding(
    text: str,
    *,
    model: str | None = None,
) -> list[float] | None:
    """
    Generate embedding vector for text.

    Args:
        text: Text to embed.
        model: Override embedding model.

    Returns:
        Embedding vector or None if not configured.
    """
    settings = get_settings()

    # Check if embeddings are enabled
    if not settings.ai.embedding_enabled:
        logger.debug("Embeddings not enabled, skipping")
        return None

    if not settings.ai.is_configured():
        logger.debug("AI not configured, skipping embedding")
        return None

    model = model or settings.ai.embedding_model
    api_key = settings.ai.get_api_key()

    try:
        if settings.ai.embedding_provider == "openai":
            return await _embed_openai(text, model, api_key, settings)
        elif settings.ai.embedding_provider == "ollama":
            return await _embed_ollama(text, model, settings)
        else:
            logger.error(
                f"Unknown embedding provider: {settings.ai.embedding_provider}"
            )
            return None
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        return None


async def _embed_openai(
    text: str,
    model: str,
    api_key: str | None,
    settings: Any,
) -> list[float] | None:
    """Generate embedding using OpenAI."""
    try:
        import httpx

        base_url = settings.ai.openai_base_url or "https://api.openai.com/v1"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "input": text,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{base_url}/embeddings",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]

    except Exception as e:
        logger.error(f"OpenAI embedding error: {e}")
        return None


async def _embed_ollama(
    text: str,
    model: str,
    settings: Any,
) -> list[float] | None:
    """Generate embedding using Ollama."""
    try:
        import httpx

        payload = {
            "model": model,
            "prompt": text,
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{settings.ai.ollama_base_url}/api/embeddings",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["embedding"]

    except Exception as e:
        logger.error(f"Ollama embedding error: {e}")
        return None


def format_prompt(
    template: str,
    instance: "SQLModel",
    source_fields: list[str],
) -> str:
    """
    Format prompt template with instance field values.

    Args:
        template: Prompt template with {field_name} placeholders.
        instance: Model instance to get values from.
        source_fields: List of source field names.

    Returns:
        Formatted prompt string.
    """
    values = {}

    for field in source_fields:
        if hasattr(instance, field):
            values[field] = getattr(instance, field) or ""

    try:
        return template.format(**values)
    except KeyError as e:
        logger.warning(f"Missing field in prompt template: {e}")
        return template


async def process_ai_fields(
    instance: "SQLModel",
    *,
    force: bool = False,
    fields: list[str] | None = None,
) -> dict[str, str | None]:
    """
    Process all AIFields on a model instance.

    This is the main entry point for AI field processing.
    Only runs if AI is enabled in settings.

    Args:
        instance: Model instance to process.
        force: Force regeneration even if value exists.
        fields: Specific fields to process (None = all).

    Returns:
        Dict of field_name -> generated value.
    """
    settings = get_settings()

    # Check if AI is enabled
    if not settings.ai.enabled:
        logger.debug("AI processing disabled in settings")
        return {}

    if not settings.ai.is_configured():
        logger.warning("AI enabled but not properly configured (missing API key?)")
        return {}

    results: dict[str, str | None] = {}

    # Get AI field metadata
    ai_fields = get_ai_field_metadata(type(instance))

    for field_name, config in ai_fields.items():
        # Skip if not in requested fields
        if fields and field_name not in fields:
            continue

        # Skip if value exists and not forcing
        current_value = getattr(instance, field_name, None)
        if current_value and not force:
            continue

        # Format prompt
        prompt = format_prompt(
            config["prompt"],
            instance,
            config["source_fields"],
        )

        # Generate content
        result = await generate_ai_content(
            prompt,
            model=config.get("model"),
            provider=config.get("provider"),
            temperature=config.get("temperature"),
            max_tokens=config.get("max_tokens"),
            use_cache=config.get("cache", True),
        )

        if result:
            setattr(instance, field_name, result)
            results[field_name] = result
        else:
            results[field_name] = None

    return results


async def process_vector_fields(
    instance: "SQLModel",
    *,
    force: bool = False,
    fields: list[str] | None = None,
) -> dict[str, list[float] | None]:
    """
    Process all VectorFields on a model instance.

    Args:
        instance: Model instance to process.
        force: Force regeneration even if value exists.
        fields: Specific fields to process (None = all).

    Returns:
        Dict of field_name -> embedding vector.
    """
    settings = get_settings()

    # Check if embeddings are enabled
    if not settings.ai.embedding_enabled:
        logger.debug("Embedding processing disabled in settings")
        return {}

    if not settings.ai.is_configured():
        logger.warning("Embeddings enabled but AI not configured")
        return {}

    results: dict[str, list[float] | None] = {}

    # Get vector field metadata
    vector_fields = get_vector_field_metadata(type(instance))

    for field_name, config in vector_fields.items():
        # Skip if not in requested fields
        if fields and field_name not in fields:
            continue

        # Skip if value exists and not forcing
        current_value = getattr(instance, field_name, None)
        if current_value and not force:
            continue

        # Get source text
        source_field = config["source_field"]
        source_text = getattr(instance, source_field, None)

        if not source_text:
            results[field_name] = None
            continue

        # Generate embedding
        result = await generate_embedding(
            source_text,
            model=config.get("model"),
        )

        if result:
            setattr(instance, field_name, result)
            results[field_name] = result
        else:
            results[field_name] = None

    return results


def has_ai_fields(model: type["SQLModel"]) -> bool:
    """Check if model has any AIFields."""
    return bool(get_ai_field_metadata(model))


def has_vector_fields(model: type["SQLModel"]) -> bool:
    """Check if model has any VectorFields."""
    return bool(get_vector_field_metadata(model))


def source_fields_changed(
    instance: "SQLModel",
    original: dict[str, Any],
    ai_field_name: str,
) -> bool:
    """
    Check if any source fields for an AIField have changed.

    Args:
        instance: Current model instance.
        original: Original field values before update.
        ai_field_name: Name of the AIField to check.

    Returns:
        True if any source field changed.
    """
    ai_fields = get_ai_field_metadata(type(instance))

    if ai_field_name not in ai_fields:
        return False

    source_fields = ai_fields[ai_field_name].get("source_fields", [])

    for field in source_fields:
        current = getattr(instance, field, None)
        orig = original.get(field)
        if current != orig:
            return True

    return False
