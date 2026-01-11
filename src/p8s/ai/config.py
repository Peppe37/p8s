"""
P8s AI Config - Model-level AI configuration.
"""

from typing import Any, Literal


class AIConfig:
    """
    AI configuration for models.

    Add this as an inner class to configure AI behavior for a model.

    Example:
        ```python
        from p8s import Model, AIField

        class Product(Model, table=True):
            name: str
            description: str

            seo_description: str = AIField(
                prompt="Generate SEO for: {description}"
            )

            class AIConfig:
                provider = "openai"
                model = "gpt-4"
                cache_ttl = 3600
        ```
    """

    # LLM provider
    provider: Literal["openai", "anthropic", "ollama", "azure", "gemini"] = "openai"

    # Default model for this type
    model: str = "gpt-4o-mini"

    # Temperature for generation
    temperature: float = 0.7

    # Maximum tokens
    max_tokens: int = 1024

    # Cache settings
    cache_enabled: bool = True
    cache_ttl: int = 3600  # seconds

    # Rate limiting
    rate_limit: int | None = None  # requests per minute

    # Retry configuration
    max_retries: int = 3
    retry_delay: float = 1.0

    # Custom system prompt for this model
    system_prompt: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AIConfig":
        """Create config from dictionary."""
        config = cls()
        for key, value in data.items():
            if hasattr(config, key):
                setattr(config, key, value)
        return config

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "provider": self.provider,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "cache_enabled": self.cache_enabled,
            "cache_ttl": self.cache_ttl,
            "rate_limit": self.rate_limit,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "system_prompt": self.system_prompt,
        }
