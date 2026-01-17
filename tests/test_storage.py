"""
Tests for cloud storage backends.
"""

from io import BytesIO

import pytest


class TestS3Storage:
    """Test S3Storage backend."""

    def test_s3_storage_import(self):
        """Test S3Storage can be imported."""
        from p8s.storage.s3 import S3Storage

        assert S3Storage is not None

    def test_s3_storage_init(self):
        """Test S3Storage initialization."""
        from p8s.storage.s3 import S3Storage

        storage = S3Storage(
            bucket_name="test-bucket",
            access_key="test-key",
            secret_key="test-secret",
            region_name="us-east-1",
        )

        assert storage.bucket_name == "test-bucket"
        assert storage.region_name == "us-east-1"

    def test_s3_storage_url_generation(self):
        """Test S3 URL generation."""
        from p8s.storage.s3 import S3Storage

        storage = S3Storage(
            bucket_name="my-bucket",
            region_name="us-east-1",
        )

        url = storage.url("uploads/photo.jpg")
        assert "my-bucket" in url
        assert "uploads/photo.jpg" in url

    def test_s3_storage_custom_domain(self):
        """Test S3 custom domain."""
        from p8s.storage.s3 import S3Storage

        storage = S3Storage(
            bucket_name="my-bucket",
            custom_domain="cdn.example.com",
        )

        url = storage.url("uploads/photo.jpg")
        assert url == "https://cdn.example.com/uploads/photo.jpg"

    def test_s3_storage_endpoint_url(self):
        """Test S3-compatible endpoint URL (MinIO, etc.)."""
        from p8s.storage.s3 import S3Storage

        storage = S3Storage(
            bucket_name="my-bucket",
            endpoint_url="http://localhost:9000",
        )

        url = storage.url("test.jpg")
        assert "localhost:9000" in url


class TestGCSStorage:
    """Test GCSStorage backend."""

    def test_gcs_storage_import(self):
        """Test GCSStorage can be imported."""
        from p8s.storage.s3 import GCSStorage

        assert GCSStorage is not None

    def test_gcs_storage_init(self):
        """Test GCSStorage initialization."""
        from p8s.storage.s3 import GCSStorage

        storage = GCSStorage(
            bucket_name="test-bucket",
            project_id="my-project",
        )

        assert storage.bucket_name == "test-bucket"
        assert storage.project_id == "my-project"

    def test_gcs_storage_url_generation(self):
        """Test GCS URL generation."""
        from p8s.storage.s3 import GCSStorage

        storage = GCSStorage(
            bucket_name="my-bucket",
        )

        url = storage.url("uploads/photo.jpg")
        assert url == "https://storage.googleapis.com/my-bucket/uploads/photo.jpg"

    def test_gcs_storage_custom_domain(self):
        """Test GCS custom domain."""
        from p8s.storage.s3 import GCSStorage

        storage = GCSStorage(
            bucket_name="my-bucket",
            custom_domain="cdn.example.com",
        )

        url = storage.url("uploads/photo.jpg")
        assert url == "https://cdn.example.com/uploads/photo.jpg"


class TestStorageBase:
    """Test base Storage class methods."""

    def test_generate_filename(self):
        """Test filename generation."""
        from p8s.storage import FileSystemStorage

        storage = FileSystemStorage()
        name = storage.generate_filename("photo.jpg", "uploads")

        assert name.startswith("uploads/")
        assert name.endswith(".jpg")
        assert len(name) > len("uploads/photo.jpg")  # Has unique ID
