"""
P8s Cloud Storage Backends - S3 and GCS storage.

Provides:
- S3Storage for AWS S3 / S3-compatible services
- GCSStorage for Google Cloud Storage

Requires optional dependencies:
    pip install boto3  # For S3
    pip install google-cloud-storage  # For GCS
"""

from typing import Any, BinaryIO

from p8s.storage.base import Storage


class S3Storage(Storage):
    """
    AWS S3 storage backend.

    Works with AWS S3 and S3-compatible services (MinIO, DigitalOcean Spaces, etc.).

    Example:
        ```python
        from p8s.storage.s3 import S3Storage

        storage = S3Storage(
            bucket_name="my-bucket",
            access_key="...",
            secret_key="...",
            region_name="us-east-1",
        )

        path = storage.save("uploads/photo.jpg", file_content)
        url = storage.url(path)  # "https://my-bucket.s3.amazonaws.com/uploads/photo.jpg"
        ```
    """

    def __init__(
        self,
        bucket_name: str,
        access_key: str | None = None,
        secret_key: str | None = None,
        region_name: str = "us-east-1",
        endpoint_url: str | None = None,
        custom_domain: str | None = None,
        default_acl: str = "public-read",
        querystring_auth: bool = False,
        querystring_expire: int = 3600,
    ) -> None:
        """
        Initialize S3 storage.

        Args:
            bucket_name: S3 bucket name.
            access_key: AWS access key (uses env/IAM if not provided).
            secret_key: AWS secret key.
            region_name: AWS region name.
            endpoint_url: Custom endpoint for S3-compatible services.
            custom_domain: Custom domain for URLs (e.g., CDN).
            default_acl: Default ACL for uploads.
            querystring_auth: Use signed URLs.
            querystring_expire: Signed URL expiration in seconds.
        """
        self.bucket_name = bucket_name
        self.region_name = region_name
        self.endpoint_url = endpoint_url
        self.custom_domain = custom_domain
        self.default_acl = default_acl
        self.querystring_auth = querystring_auth
        self.querystring_expire = querystring_expire

        self._client = None
        self._access_key = access_key
        self._secret_key = secret_key

    def _get_client(self):
        """Lazy-load boto3 client."""
        if self._client is None:
            try:
                import boto3
            except ImportError:
                raise ImportError(
                    "boto3 is required for S3Storage. "
                    "Install it with: pip install boto3"
                )

            kwargs = {
                "service_name": "s3",
                "region_name": self.region_name,
            }

            if self._access_key and self._secret_key:
                kwargs["aws_access_key_id"] = self._access_key
                kwargs["aws_secret_access_key"] = self._secret_key

            if self.endpoint_url:
                kwargs["endpoint_url"] = self.endpoint_url

            self._client = boto3.client(**kwargs)

        return self._client

    def save(self, name: str, content: BinaryIO, **kwargs: Any) -> str:
        """
        Upload a file to S3.

        Args:
            name: File path/key in the bucket.
            content: File content as binary stream.
            **kwargs: Additional options (content_type, acl, etc.)

        Returns:
            The S3 key where the file was saved.
        """
        client = self._get_client()

        extra_args = {
            "ACL": kwargs.get("acl", self.default_acl),
        }

        if "content_type" in kwargs:
            extra_args["ContentType"] = kwargs["content_type"]

        client.upload_fileobj(
            content,
            self.bucket_name,
            name,
            ExtraArgs=extra_args,
        )

        return name

    def delete(self, name: str) -> bool:
        """Delete a file from S3."""
        client = self._get_client()

        try:
            client.delete_object(Bucket=self.bucket_name, Key=name)
            return True
        except Exception:
            return False

    def exists(self, name: str) -> bool:
        """Check if a file exists in S3."""
        client = self._get_client()

        try:
            client.head_object(Bucket=self.bucket_name, Key=name)
            return True
        except Exception:
            return False

    def url(self, name: str) -> str:
        """
        Get the URL for a file.

        If querystring_auth is True, returns a presigned URL.
        Otherwise, returns a public URL.
        """
        if self.custom_domain:
            return f"https://{self.custom_domain}/{name}"

        if self.querystring_auth:
            client = self._get_client()
            return client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": name},
                ExpiresIn=self.querystring_expire,
            )

        if self.endpoint_url:
            return f"{self.endpoint_url}/{self.bucket_name}/{name}"

        return f"https://{self.bucket_name}.s3.{self.region_name}.amazonaws.com/{name}"

    def size(self, name: str) -> int:
        """Get file size in bytes."""
        client = self._get_client()

        response = client.head_object(Bucket=self.bucket_name, Key=name)
        return response["ContentLength"]


class GCSStorage(Storage):
    """
    Google Cloud Storage backend.

    Example:
        ```python
        from p8s.storage.s3 import GCSStorage

        storage = GCSStorage(
            bucket_name="my-bucket",
            project_id="my-project",
        )

        path = storage.save("uploads/photo.jpg", file_content)
        url = storage.url(path)
        ```
    """

    def __init__(
        self,
        bucket_name: str,
        project_id: str | None = None,
        credentials_file: str | None = None,
        custom_domain: str | None = None,
        default_acl: str | None = None,
    ) -> None:
        """
        Initialize GCS storage.

        Args:
            bucket_name: GCS bucket name.
            project_id: Google Cloud project ID.
            credentials_file: Path to service account JSON.
            custom_domain: Custom domain for URLs.
            default_acl: Default ACL for uploads.
        """
        self.bucket_name = bucket_name
        self.project_id = project_id
        self.credentials_file = credentials_file
        self.custom_domain = custom_domain
        self.default_acl = default_acl

        self._client = None
        self._bucket = None

    def _get_bucket(self):
        """Lazy-load GCS bucket."""
        if self._bucket is None:
            try:
                from google.cloud import storage as gcs
            except ImportError:
                raise ImportError(
                    "google-cloud-storage is required for GCSStorage. "
                    "Install it with: pip install google-cloud-storage"
                )

            if self.credentials_file:
                self._client = gcs.Client.from_service_account_json(
                    self.credentials_file,
                    project=self.project_id,
                )
            else:
                self._client = gcs.Client(project=self.project_id)

            self._bucket = self._client.bucket(self.bucket_name)

        return self._bucket

    def save(self, name: str, content: BinaryIO, **kwargs: Any) -> str:
        """Upload a file to GCS."""
        bucket = self._get_bucket()
        blob = bucket.blob(name)

        if "content_type" in kwargs:
            blob.content_type = kwargs["content_type"]

        blob.upload_from_file(content)

        if self.default_acl:
            blob.acl.save_predefined(self.default_acl)

        return name

    def delete(self, name: str) -> bool:
        """Delete a file from GCS."""
        bucket = self._get_bucket()
        blob = bucket.blob(name)

        try:
            blob.delete()
            return True
        except Exception:
            return False

    def exists(self, name: str) -> bool:
        """Check if a file exists in GCS."""
        bucket = self._get_bucket()
        blob = bucket.blob(name)
        return blob.exists()

    def url(self, name: str) -> str:
        """Get the URL for a file."""
        if self.custom_domain:
            return f"https://{self.custom_domain}/{name}"

        return f"https://storage.googleapis.com/{self.bucket_name}/{name}"

    def size(self, name: str) -> int:
        """Get file size in bytes."""
        bucket = self._get_bucket()
        blob = bucket.blob(name)
        blob.reload()
        return blob.size or 0
