"""
P8s AI Module - AI/LLM integration.

All AI features are opt-in and configured via settings.
Enable with P8S_AI_ENABLED=true in your environment.
"""

from p8s.ai.client import AIClient
from p8s.ai.config import AIConfig
from p8s.ai.fields import AIField, VectorField
from p8s.ai.processor import (
    generate_ai_content,
    generate_embedding,
    has_ai_fields,
    has_vector_fields,
    process_ai_fields,
    process_vector_fields,
)
from p8s.ai.vector_search import (
    VectorSearch,
    VectorSearchError,
    create_vector_search,
    ensure_pgvector_extension,
)

__all__ = [
    # Fields
    "AIField",
    "VectorField",
    # Client (legacy)
    "AIClient",
    "AIConfig",
    # Processor
    "process_ai_fields",
    "process_vector_fields",
    "generate_ai_content",
    "generate_embedding",
    "has_ai_fields",
    "has_vector_fields",
    # Vector Search
    "VectorSearch",
    "VectorSearchError",
    "create_vector_search",
    "ensure_pgvector_extension",
]
