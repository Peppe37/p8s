"""
P8s AI Fields - AI-powered model fields.

These fields automatically generate content using LLMs.
"""

from typing import Any

from pydantic import Field
from pydantic.fields import FieldInfo


class AIFieldInfo(FieldInfo):
    """
    Extended FieldInfo for AI-generated fields.
    """

    def __init__(
        self,
        prompt: str,
        *,
        source_fields: list[str] | None = None,
        model: str | None = None,
        cache: bool = True,
        regenerate_on_change: bool = True,
        default: Any = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize AI field.

        Args:
            prompt: The prompt template. Use {field_name} for interpolation.
            source_fields: Fields that trigger regeneration when changed.
            model: Override the default LLM model.
            cache: Whether to cache the generated value.
            regenerate_on_change: Regenerate when source fields change.
            default: Default value before generation.
            **kwargs: Additional Field arguments.
        """
        super().__init__(default=default, **kwargs)
        self.prompt = prompt
        self.source_fields = source_fields or []
        self.ai_model = model
        self.cache = cache
        self.regenerate_on_change = regenerate_on_change


def AIField(
    prompt: str,
    *,
    source_fields: list[str] | None = None,
    model: str | None = None,
    cache: bool = True,
    regenerate_on_change: bool = True,
    default: Any = None,
    description: str | None = None,
    **kwargs: Any,
) -> Any:
    """
    Create an AI-generated field.

    The field value will be automatically generated using an LLM
    based on the provided prompt template.

    Example:
        ```python
        from p8s import Model, AIField

        class Product(Model, table=True):
            name: str
            description: str

            # Auto-generated SEO description
            seo_description: str = AIField(
                prompt="Generate an SEO-optimized description for: {description}",
                source_fields=["description"],
            )
        ```

    Args:
        prompt: The prompt template. Use {field_name} to interpolate model fields.
        source_fields: Fields that trigger regeneration when changed.
        model: Override the default LLM model from settings.
        cache: Whether to cache the generated value (default: True).
        regenerate_on_change: Regenerate when source fields change (default: True).
        default: Default value before generation.
        description: Field description for documentation.
        **kwargs: Additional Field arguments.

    Returns:
        A Pydantic field with AI generation capabilities.
    """
    return Field(
        default=default,
        description=description or f"AI-generated field using prompt: {prompt[:50]}...",
        json_schema_extra={
            "x-p8s-ai-field": True,
            "x-p8s-ai-prompt": prompt,
            "x-p8s-ai-source-fields": source_fields or [],
            "x-p8s-ai-model": model,
            "x-p8s-ai-cache": cache,
            "x-p8s-ai-regenerate": regenerate_on_change,
        },
        **kwargs,
    )


class VectorFieldInfo(FieldInfo):
    """
    Extended FieldInfo for vector embedding fields.
    """

    def __init__(
        self,
        source_field: str,
        *,
        dimensions: int = 1536,
        model: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(default=None, **kwargs)
        self.source_field = source_field
        self.dimensions = dimensions
        self.embedding_model = model


def VectorField(
    source_field: str,
    *,
    dimensions: int = 1536,
    model: str | None = None,
    description: str | None = None,
    **kwargs: Any,
) -> Any:
    """
    Create a vector embedding field for RAG/similarity search.

    The field automatically generates embeddings from the source field
    and stores them for vector similarity search.

    Example:
        ```python
        from p8s import Model, VectorField

        class Document(Model, table=True):
            content: str

            # Auto-generated embedding for similarity search
            embedding: list[float] = VectorField(
                source_field="content",
                dimensions=1536,
            )
        ```

    Args:
        source_field: The field to generate embeddings from.
        dimensions: Embedding dimensions (default: 1536 for OpenAI).
        model: Override the default embedding model.
        description: Field description.
        **kwargs: Additional Field arguments.

    Returns:
        A Pydantic field with vector embedding capabilities.

    Note:
        Requires pgvector extension for PostgreSQL.
    """
    from sqlalchemy import JSON, Column

    return Field(
        default=None,
        description=description or f"Vector embedding from {source_field}",
        sa_column=Column(JSON),
        json_schema_extra={
            "x-p8s-vector-field": True,
            "x-p8s-vector-source": source_field,
            "x-p8s-vector-dimensions": dimensions,
            "x-p8s-vector-model": model,
        },
        **kwargs,
    )


async def generate_ai_field(
    model_instance: Any,
    field_name: str,
    prompt: str,
    ai_model: str | None = None,
) -> str:
    """
    Generate value for an AI field.

    Args:
        model_instance: The model instance.
        field_name: Name of the field to generate.
        prompt: Prompt template.
        ai_model: LLM model to use.

    Returns:
        Generated string value.
    """
    from p8s.ai.client import get_ai_client

    # Interpolate prompt with model fields
    model_data = model_instance.model_dump()
    formatted_prompt = prompt.format(**model_data)

    client = get_ai_client()
    response = await client.generate(
        prompt=formatted_prompt,
        model=ai_model,
    )

    return response


async def generate_embedding(
    text: str,
    model: str | None = None,
    dimensions: int = 1536,
) -> list[float]:
    """
    Generate embedding vector for text.

    Args:
        text: Text to embed.
        model: Embedding model to use.
        dimensions: Expected dimensions.

    Returns:
        List of floats representing the embedding.
    """
    from p8s.ai.client import get_ai_client

    client = get_ai_client()
    return await client.embed(text, model=model)
