"""
P8s Vector Search - Similarity search using pgvector.

Provides vector similarity search capabilities for models with VectorField.
Requires PostgreSQL with pgvector extension for production use.
"""

import logging
from typing import TYPE_CHECKING, Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from p8s.core.settings import get_settings

if TYPE_CHECKING:
    from sqlmodel import SQLModel

logger = logging.getLogger("p8s.vector")

ModelType = TypeVar("ModelType", bound="SQLModel")


class VectorSearchError(Exception):
    """Error during vector search operation."""

    pass


class VectorSearch(Generic[ModelType]):
    """
    Vector similarity search for SQLModel models.

    Supports multiple similarity metrics:
    - cosine: Cosine similarity (default, recommended for normalized embeddings)
    - l2: Euclidean distance
    - inner_product: Inner product (dot product)

    Example:
        ```python
        from p8s.ai.vector_search import VectorSearch
        from myapp.models import Document

        # Initialize search
        search = VectorSearch(Document, vector_field="embedding")

        # Find similar documents
        results = await search.similar(
            session,
            query="What is machine learning?",
            limit=10,
        )

        # Or use a pre-computed embedding
        results = await search.similar_by_vector(
            session,
            embedding=[0.1, 0.2, ...],
            limit=10,
        )
        ```
    """

    def __init__(
        self,
        model: type[ModelType],
        vector_field: str = "embedding",
        *,
        metric: str = "cosine",
    ) -> None:
        """
        Initialize vector search.

        Args:
            model: The SQLModel class with a VectorField.
            vector_field: Name of the vector field to search.
            metric: Similarity metric ('cosine', 'l2', 'inner_product').
        """
        self.model = model
        self.vector_field = vector_field
        self.metric = metric

        # Validate vector field exists (check model_fields for SQLModel)
        if vector_field not in model.model_fields:
            raise VectorSearchError(
                f"Model {model.__name__} has no field '{vector_field}'"
            )

    def _get_distance_operator(self) -> str:
        """Get pgvector distance operator for the metric."""
        operators = {
            "cosine": "<=>",  # Cosine distance
            "l2": "<->",  # Euclidean distance
            "inner_product": "<#>",  # Negative inner product
        }

        if self.metric not in operators:
            raise VectorSearchError(
                f"Unknown metric: {self.metric}. Use one of: {list(operators.keys())}"
            )

        return operators[self.metric]

    async def similar(
        self,
        session: AsyncSession,
        query: str,
        *,
        limit: int = 10,
        threshold: float | None = None,
        filters: dict[str, Any] | None = None,
        include_deleted: bool = False,
    ) -> list[tuple[ModelType, float]]:
        """
        Find similar items by text query.

        Generates an embedding for the query and searches for similar items.

        Args:
            session: Database session.
            query: Text query to search for.
            limit: Maximum number of results.
            threshold: Maximum distance threshold (lower = more similar).
            filters: Additional field filters (e.g., {"category": "tech"}).
            include_deleted: Include soft-deleted items.

        Returns:
            List of (model_instance, distance) tuples, sorted by similarity.
        """
        from p8s.ai.processor import generate_embedding

        settings = get_settings()

        # Check if embeddings are enabled
        if not settings.ai.embedding_enabled:
            logger.warning("Embeddings not enabled, using fallback text search")
            return await self._fallback_text_search(
                session, query, limit, filters, include_deleted
            )

        # Generate embedding for query
        embedding = await generate_embedding(query)

        if not embedding:
            logger.warning("Failed to generate embedding, using fallback")
            return await self._fallback_text_search(
                session, query, limit, filters, include_deleted
            )

        return await self.similar_by_vector(
            session,
            embedding,
            limit=limit,
            threshold=threshold,
            filters=filters,
            include_deleted=include_deleted,
        )

    async def similar_by_vector(
        self,
        session: AsyncSession,
        embedding: list[float],
        *,
        limit: int = 10,
        threshold: float | None = None,
        filters: dict[str, Any] | None = None,
        include_deleted: bool = False,
    ) -> list[tuple[ModelType, float]]:
        """
        Find similar items by embedding vector.

        Args:
            session: Database session.
            embedding: Query embedding vector.
            limit: Maximum number of results.
            threshold: Maximum distance threshold.
            filters: Additional field filters.
            include_deleted: Include soft-deleted items.

        Returns:
            List of (model_instance, distance) tuples, sorted by similarity.
        """
        settings = get_settings()
        operator = self._get_distance_operator()

        # Build query
        table_name = self.model.__tablename__
        vector_col = self.vector_field

        # Convert embedding to pgvector format
        vector_str = "[" + ",".join(map(str, embedding)) + "]"

        # Check database type
        db_url = settings.database.url.lower()

        if "postgresql" in db_url:
            # Use pgvector native operators
            return await self._search_pgvector(
                session,
                vector_str,
                operator,
                limit,
                threshold,
                filters,
                include_deleted,
            )
        else:
            # Fallback: compute distance in Python for SQLite/others
            return await self._search_python(
                session,
                embedding,
                limit,
                threshold,
                filters,
                include_deleted,
            )

    async def _search_pgvector(
        self,
        session: AsyncSession,
        vector_str: str,
        operator: str,
        limit: int,
        threshold: float | None,
        filters: dict[str, Any] | None,
        include_deleted: bool,
    ) -> list[tuple[ModelType, float]]:
        """Search using native pgvector operators."""
        table_name = self.model.__tablename__
        vector_col = self.vector_field

        # Build WHERE clauses
        where_clauses = []

        # Soft delete filter
        if hasattr(self.model, "deleted_at") and not include_deleted:
            where_clauses.append(f"{table_name}.deleted_at IS NULL")

        # Null embedding filter
        where_clauses.append(f"{table_name}.{vector_col} IS NOT NULL")

        # Custom filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    if isinstance(value, str):
                        where_clauses.append(f"{table_name}.{field} = '{value}'")
                    elif value is None:
                        where_clauses.append(f"{table_name}.{field} IS NULL")
                    else:
                        where_clauses.append(f"{table_name}.{field} = {value}")

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Distance threshold
        having_sql = ""
        if threshold is not None:
            having_sql = f"HAVING {vector_col} {operator} '{vector_str}' < {threshold}"

        # Build query
        sql = f"""
            SELECT *, ({vector_col} {operator} '{vector_str}') as distance
            FROM {table_name}
            WHERE {where_sql}
            ORDER BY distance ASC
            LIMIT {limit}
        """

        try:
            result = await session.execute(text(sql))
            rows = result.fetchall()

            # Convert to model instances
            results = []
            for row in rows:
                # Create model instance from row
                row_dict = dict(row._mapping)
                distance = row_dict.pop("distance", 0.0)
                instance = self.model(**row_dict)
                results.append((instance, float(distance)))

            return results

        except Exception as e:
            logger.error(f"pgvector search failed: {e}")
            raise VectorSearchError(f"Vector search failed: {e}")

    async def _search_python(
        self,
        session: AsyncSession,
        query_embedding: list[float],
        limit: int,
        threshold: float | None,
        filters: dict[str, Any] | None,
        include_deleted: bool,
    ) -> list[tuple[ModelType, float]]:
        """Fallback: search using Python-computed distances."""

        # Build query
        query = select(self.model)

        # Soft delete filter
        if hasattr(self.model, "deleted_at") and not include_deleted:
            query = query.where(self.model.deleted_at.is_(None))

        # Custom filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)

        result = await session.execute(query)
        items = result.scalars().all()

        # Compute distances
        scored_items = []

        for item in items:
            embedding = getattr(item, self.vector_field, None)
            if not embedding:
                continue

            distance = self._compute_distance(query_embedding, embedding)

            if threshold is None or distance < threshold:
                scored_items.append((item, distance))

        # Sort by distance and limit
        scored_items.sort(key=lambda x: x[1])

        return scored_items[:limit]

    def _compute_distance(
        self,
        a: list[float],
        b: list[float],
    ) -> float:
        """Compute distance between two vectors."""
        import math

        if len(a) != len(b):
            raise VectorSearchError(f"Vector dimension mismatch: {len(a)} vs {len(b)}")

        if self.metric == "cosine":
            # Cosine distance = 1 - cosine_similarity
            dot = sum(x * y for x, y in zip(a, b))
            norm_a = math.sqrt(sum(x * x for x in a))
            norm_b = math.sqrt(sum(x * x for x in b))

            if norm_a == 0 or norm_b == 0:
                return 1.0

            similarity = dot / (norm_a * norm_b)
            return 1 - similarity

        elif self.metric == "l2":
            # Euclidean distance
            return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

        elif self.metric == "inner_product":
            # Negative inner product (for max similarity)
            return -sum(x * y for x, y in zip(a, b))

        raise VectorSearchError(f"Unknown metric: {self.metric}")

    async def _fallback_text_search(
        self,
        session: AsyncSession,
        query: str,
        limit: int,
        filters: dict[str, Any] | None,
        include_deleted: bool,
    ) -> list[tuple[ModelType, float]]:
        """Fallback to basic text matching when embeddings unavailable."""
        from sqlalchemy import or_

        # Find text fields to search
        text_fields = []
        for field_name, field_info in self.model.model_fields.items():
            annotation = field_info.annotation
            if annotation in (str, str | None):
                text_fields.append(field_name)

        if not text_fields:
            logger.warning("No text fields found for fallback search")
            return []

        # Build query
        q = select(self.model)

        # Soft delete filter
        if hasattr(self.model, "deleted_at") and not include_deleted:
            q = q.where(self.model.deleted_at.is_(None))

        # Text search (LIKE matching)
        search_pattern = f"%{query}%"
        conditions = [
            getattr(self.model, field).ilike(search_pattern)
            for field in text_fields
            if hasattr(self.model, field)
        ]

        if conditions:
            q = q.where(or_(*conditions))

        # Custom filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    q = q.where(getattr(self.model, field) == value)

        q = q.limit(limit)

        result = await session.execute(q)
        items = result.scalars().all()

        # Return with fake distance (0 = exact match placeholder)
        return [(item, 0.0) for item in items]

    async def similar_to_id(
        self,
        session: AsyncSession,
        id: UUID,
        *,
        limit: int = 10,
        exclude_self: bool = True,
        threshold: float | None = None,
        filters: dict[str, Any] | None = None,
        include_deleted: bool = False,
    ) -> list[tuple[ModelType, float]]:
        """
        Find items similar to a given item by ID.

        Args:
            session: Database session.
            id: ID of the item to find similar items for.
            limit: Maximum number of results.
            exclude_self: Exclude the source item from results.
            threshold: Maximum distance threshold.
            filters: Additional field filters.
            include_deleted: Include soft-deleted items.

        Returns:
            List of (model_instance, distance) tuples.
        """
        # Get source item
        query = select(self.model).where(self.model.id == id)
        result = await session.execute(query)
        source = result.scalar_one_or_none()

        if not source:
            raise VectorSearchError(f"Item with id {id} not found")

        embedding = getattr(source, self.vector_field, None)

        if not embedding:
            raise VectorSearchError(
                f"Item {id} has no embedding in field '{self.vector_field}'"
            )

        # Get actual limit (account for exclusion)
        search_limit = limit + 1 if exclude_self else limit

        results = await self.similar_by_vector(
            session,
            embedding,
            limit=search_limit,
            threshold=threshold,
            filters=filters,
            include_deleted=include_deleted,
        )

        # Filter out self if needed
        if exclude_self:
            results = [(item, dist) for item, dist in results if item.id != id]
            results = results[:limit]

        return results


def create_vector_search(
    model: type[ModelType],
    vector_field: str = "embedding",
    metric: str = "cosine",
) -> VectorSearch[ModelType]:
    """
    Factory function to create a VectorSearch instance.

    Args:
        model: The SQLModel class with a VectorField.
        vector_field: Name of the vector field.
        metric: Similarity metric.

    Returns:
        VectorSearch instance.
    """
    return VectorSearch(model, vector_field, metric=metric)


async def ensure_pgvector_extension(session: AsyncSession) -> bool:
    """
    Ensure pgvector extension is installed (PostgreSQL only).

    Args:
        session: Database session.

    Returns:
        True if extension is available.
    """
    settings = get_settings()

    if "postgresql" not in settings.database.url.lower():
        logger.debug("Not PostgreSQL, skipping pgvector check")
        return False

    try:
        await session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await session.commit()
        logger.info("pgvector extension enabled")
        return True
    except Exception as e:
        logger.warning(f"Could not enable pgvector: {e}")
        return False
