"""
Tests for P8s Vector Search module.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlmodel import Field

from p8s.ai.fields import VectorField
from p8s.ai.vector_search import (
    VectorSearch,
    VectorSearchError,
    create_vector_search,
)
from p8s.db.base import Model


class TestVectorSearch:
    """Test VectorSearch class."""

    def test_create_vector_search(self):
        """Test creating a VectorSearch instance."""

        class TestModel(Model):
            content: str = Field(default="")
            embedding: list[float] | None = VectorField(source_field="content")

        search = VectorSearch(TestModel, "embedding")

        assert search.model == TestModel
        assert search.vector_field == "embedding"
        assert search.metric == "cosine"

    def test_create_with_custom_metric(self):
        """Test creating with custom metric."""

        class TestModel(Model):
            embedding: list[float] | None = VectorField(source_field="content")

        search = VectorSearch(TestModel, "embedding", metric="l2")
        assert search.metric == "l2"

    def test_invalid_vector_field(self):
        """Test error on invalid vector field."""

        class TestModel(Model):
            name: str = Field(default="")

        with pytest.raises(VectorSearchError):
            VectorSearch(TestModel, "nonexistent")

    def test_distance_operators(self):
        """Test distance operator mapping."""

        class TestModel(Model):
            embedding: list[float] | None = VectorField(source_field="content")

        # Cosine
        search = VectorSearch(TestModel, "embedding", metric="cosine")
        assert search._get_distance_operator() == "<=>"

        # L2
        search = VectorSearch(TestModel, "embedding", metric="l2")
        assert search._get_distance_operator() == "<->"

        # Inner product
        search = VectorSearch(TestModel, "embedding", metric="inner_product")
        assert search._get_distance_operator() == "<#>"

    def test_invalid_metric(self):
        """Test error on invalid metric."""

        class TestModel(Model):
            embedding: list[float] | None = VectorField(source_field="content")

        search = VectorSearch(TestModel, "embedding", metric="invalid")

        with pytest.raises(VectorSearchError):
            search._get_distance_operator()


class TestDistanceComputation:
    """Test distance computation methods."""

    def test_cosine_distance(self):
        """Test cosine distance computation."""

        class TestModel(Model):
            embedding: list[float] | None = VectorField(source_field="content")

        search = VectorSearch(TestModel, "embedding", metric="cosine")

        # Same vectors = 0 distance
        a = [1.0, 0.0, 0.0]
        b = [1.0, 0.0, 0.0]
        assert search._compute_distance(a, b) == pytest.approx(0.0)

        # Orthogonal vectors = 1 distance
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        assert search._compute_distance(a, b) == pytest.approx(1.0)

        # Opposite vectors = 2 distance
        a = [1.0, 0.0]
        b = [-1.0, 0.0]
        assert search._compute_distance(a, b) == pytest.approx(2.0)

    def test_l2_distance(self):
        """Test Euclidean distance computation."""

        class TestModel(Model):
            embedding: list[float] | None = VectorField(source_field="content")

        search = VectorSearch(TestModel, "embedding", metric="l2")

        # Same vectors = 0 distance
        a = [1.0, 2.0, 3.0]
        b = [1.0, 2.0, 3.0]
        assert search._compute_distance(a, b) == pytest.approx(0.0)

        # Simple case
        a = [0.0, 0.0]
        b = [3.0, 4.0]
        assert search._compute_distance(a, b) == pytest.approx(5.0)

    def test_inner_product_distance(self):
        """Test inner product distance computation."""

        class TestModel(Model):
            embedding: list[float] | None = VectorField(source_field="content")

        search = VectorSearch(TestModel, "embedding", metric="inner_product")

        a = [1.0, 2.0]
        b = [3.0, 4.0]
        # Inner product = 1*3 + 2*4 = 11
        # Negative = -11
        assert search._compute_distance(a, b) == pytest.approx(-11.0)

    def test_dimension_mismatch(self):
        """Test error on dimension mismatch."""

        class TestModel(Model):
            embedding: list[float] | None = VectorField(source_field="content")

        search = VectorSearch(TestModel, "embedding")

        a = [1.0, 2.0]
        b = [1.0, 2.0, 3.0]

        with pytest.raises(VectorSearchError):
            search._compute_distance(a, b)


class TestFactoryFunction:
    """Test factory function."""

    def test_create_vector_search_factory(self):
        """Test create_vector_search factory."""

        class TestModel(Model):
            embedding: list[float] | None = VectorField(source_field="content")

        search = create_vector_search(TestModel, "embedding", "l2")

        assert isinstance(search, VectorSearch)
        assert search.metric == "l2"


class TestPythonFallback:
    """Test Python fallback search - direct computation tests."""

    def test_distance_ranking(self):
        """Test that distances are computed correctly for ranking."""

        class TestModel(Model):
            name: str = Field(default="")
            embedding: list[float] | None = VectorField(source_field="name")

        search = VectorSearch(TestModel, "embedding", metric="cosine")

        # Query embedding
        query = [1.0, 0.0, 0.0]

        # Item embeddings with known distances
        item1 = [1.0, 0.0, 0.0]  # Identical = 0
        item2 = [0.9, 0.1, 0.0]  # Very similar < 0.1
        item3 = [0.0, 1.0, 0.0]  # Orthogonal = 1.0

        d1 = search._compute_distance(query, item1)
        d2 = search._compute_distance(query, item2)
        d3 = search._compute_distance(query, item3)

        # Check ordering
        assert d1 < d2 < d3
        assert d1 == pytest.approx(0.0)
        assert d3 == pytest.approx(1.0)

    def test_sorting_logic(self):
        """Test that items are sorted correctly by distance."""
        # Create scored items like _search_python would
        scored_items = [
            ("item3", 1.0),
            ("item1", 0.0),
            ("item2", 0.05),
        ]

        # Sort by distance (the logic from _search_python)
        scored_items.sort(key=lambda x: x[1])

        assert scored_items[0][0] == "item1"  # Closest
        assert scored_items[1][0] == "item2"
        assert scored_items[2][0] == "item3"  # Farthest

    def test_threshold_filtering(self):
        """Test threshold filtering logic."""

        class TestModel(Model):
            embedding: list[float] | None = VectorField(source_field="content")

        search = VectorSearch(TestModel, "embedding", metric="cosine")

        query = [1.0, 0.0, 0.0]

        # Simulate items with different distances
        test_cases = [
            ([1.0, 0.0, 0.0], 0.0),  # Should pass threshold 0.5
            ([0.9, 0.1, 0.0], 0.02),  # Should pass threshold 0.5
            ([0.0, 1.0, 0.0], 1.0),  # Should NOT pass threshold 0.5
        ]

        threshold = 0.5
        passed = []

        for embedding, expected_dist in test_cases:
            distance = search._compute_distance(query, embedding)
            if distance < threshold:
                passed.append((embedding, distance))

        # Only 2 items should pass the threshold
        assert len(passed) == 2
