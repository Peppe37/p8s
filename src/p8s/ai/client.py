"""
P8s AI Client - Provider-agnostic LLM client.

Uses LiteLLM under the hood for unified API access.
"""

from functools import lru_cache
from typing import Any

from p8s.core.settings import AISettings, get_settings


class AIClient:
    """
    Provider-agnostic AI client.

    Supports:
    - OpenAI (GPT-4, GPT-3.5)
    - Anthropic (Claude)
    - Google (Gemini)
    - Azure OpenAI
    - Ollama (local models)

    Example:
        ```python
        from p8s.ai import AIClient

        client = AIClient()

        # Generate text
        response = await client.generate("Write a poem about Python")

        # Generate structured output
        product = await client.generate_structured(
            "Create a product",
            response_model=ProductSchema,
        )

        # Generate embeddings
        embedding = await client.embed("Hello world")
        ```
    """

    def __init__(self, settings: AISettings | None = None) -> None:
        """
        Initialize AI client.

        Args:
            settings: AI settings. If None, loads from environment.
        """
        self.settings = settings or get_settings().ai
        self._setup_provider()

    def _setup_provider(self) -> None:
        """Configure the LLM provider."""
        import os

        # Set API keys from settings
        if self.settings.openai_api_key:
            os.environ["OPENAI_API_KEY"] = self.settings.openai_api_key
        if self.settings.anthropic_api_key:
            os.environ["ANTHROPIC_API_KEY"] = self.settings.anthropic_api_key
        if self.settings.gemini_api_key:
            os.environ["GEMINI_API_KEY"] = self.settings.gemini_api_key
        if self.settings.azure_api_key:
            os.environ["AZURE_API_KEY"] = self.settings.azure_api_key

    def _get_model_name(self, model: str | None = None) -> str:
        """Get the full model name for LiteLLM."""
        model = model or self.settings.model
        provider = self.settings.provider

        # LiteLLM model name format
        if provider == "openai":
            return model
        elif provider == "anthropic":
            return f"anthropic/{model}"
        elif provider == "gemini":
            return f"gemini/{model}"
        elif provider == "azure":
            return f"azure/{model}"
        elif provider == "ollama":
            return f"ollama/{model}"

        return model

    async def generate(
        self,
        prompt: str,
        *,
        model: str | None = None,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> str:
        """
        Generate text using LLM.

        Args:
            prompt: The user prompt.
            model: Override the default model.
            system_prompt: Optional system prompt.
            temperature: Sampling temperature (0-2).
            max_tokens: Maximum tokens in response.
            **kwargs: Additional provider-specific arguments.

        Returns:
            Generated text.
        """
        try:
            import litellm

            messages = []

            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            messages.append({"role": "user", "content": prompt})

            response = await litellm.acompletion(
                model=self._get_model_name(model),
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

            return response.choices[0].message.content

        except ImportError:
            raise ImportError(
                "LiteLLM is required for AI features. Install with: pip install p8s[ai]"
            )

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> str:
        """
        Chat completion using list of messages.

        Args:
            messages: List of message dicts (role, content).
            model: Override the default model.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in response.
            **kwargs: Additional provider-specific arguments.

        Returns:
            Generated response content.
        """
        try:
            import litellm

            response = await litellm.acompletion(
                model=self._get_model_name(model),
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

            return response.choices[0].message.content

        except ImportError:
            raise ImportError(
                "LiteLLM is required for AI features. Install with: pip install p8s[ai]"
            )

    async def generate_structured(
        self,
        prompt: str,
        response_model: type[Any],
        *,
        model: str | None = None,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> Any:
        """
        Generate structured output using Instructor.

        Args:
            prompt: The user prompt.
            response_model: Pydantic model for the response.
            model: Override the default model.
            system_prompt: Optional system prompt.
            **kwargs: Additional arguments.

        Returns:
            An instance of response_model.
        """
        try:
            import instructor
            import litellm

            client = instructor.from_litellm(litellm.acompletion)

            messages = []

            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            messages.append({"role": "user", "content": prompt})

            return await client.chat.completions.create(
                model=self._get_model_name(model),
                messages=messages,
                response_model=response_model,
                **kwargs,
            )

        except ImportError:
            raise ImportError(
                "Instructor is required for structured outputs. "
                "Install with: pip install p8s[ai]"
            )

    async def embed(
        self,
        text: str,
        *,
        model: str | None = None,
    ) -> list[float]:
        """
        Generate embedding for text.

        Args:
            text: Text to embed.
            model: Override the default embedding model.

        Returns:
            Embedding vector as list of floats.
        """
        try:
            import litellm

            model = model or self.settings.embedding_model

            response = await litellm.aembedding(
                model=model,
                input=[text],
            )

            return response.data[0]["embedding"]

        except ImportError:
            raise ImportError(
                "LiteLLM is required for embeddings. Install with: pip install p8s[ai]"
            )

    async def embed_batch(
        self,
        texts: list[str],
        *,
        model: str | None = None,
    ) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed.
            model: Override the default embedding model.

        Returns:
            List of embedding vectors.
        """
        try:
            import litellm

            model = model or self.settings.embedding_model

            response = await litellm.aembedding(
                model=model,
                input=texts,
            )

            return [item["embedding"] for item in response.data]

        except ImportError:
            raise ImportError(
                "LiteLLM is required for embeddings. Install with: pip install p8s[ai]"
            )

    async def stream(
        self,
        prompt: str,
        *,
        model: str | None = None,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ):
        """
        Stream text generation.

        Args:
            prompt: The user prompt.
            model: Override the default model.
            system_prompt: Optional system prompt.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens.
            **kwargs: Additional arguments.

        Yields:
            String chunks as they are generated.
        """
        try:
            import litellm

            messages = []

            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            messages.append({"role": "user", "content": prompt})

            response = await litellm.acompletion(
                model=self._get_model_name(model),
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs,
            )

            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except ImportError:
            raise ImportError(
                "LiteLLM is required for AI features. Install with: pip install p8s[ai]"
            )


@lru_cache
def get_ai_client() -> AIClient:
    """
    Get cached AI client instance.

    Returns:
        AIClient: Configured AI client.
    """
    return AIClient()
