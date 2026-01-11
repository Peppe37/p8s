"""
P8s Storage Fields - FileField and ImageField for models.

Provides Django-style file fields that:
- Store file paths in the database
- Handle file uploads automatically
- Integrate with storage backends
"""

from io import BytesIO
from typing import Any

from pydantic.fields import FieldInfo
from sqlmodel import Field

from p8s.storage.base import Storage, get_default_storage


class FileFieldInfo(FieldInfo):
    """Extended FieldInfo for file fields."""

    def __init__(
        self,
        upload_to: str = "",
        storage: Storage | None = None,
        max_size: int | None = None,
        allowed_extensions: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize file field.

        Args:
            upload_to: Subdirectory for uploads (e.g., "documents/")
            storage: Storage backend (defaults to FileSystemStorage)
            max_size: Maximum file size in bytes
            allowed_extensions: List of allowed extensions (e.g., [".pdf", ".doc"])
            **kwargs: Additional Field arguments
        """
        super().__init__(default=None, **kwargs)
        self.upload_to = upload_to
        self.storage = storage
        self.max_size = max_size
        self.allowed_extensions = allowed_extensions


def FileField(
    upload_to: str = "",
    storage: Storage | None = None,
    max_size: int | None = None,
    allowed_extensions: list[str] | None = None,
    description: str | None = None,
    **kwargs: Any,
) -> Any:
    """
    Create a file field for storing uploaded files.

    The field stores the file path in the database, while the actual
    file is stored using the configured storage backend.

    Example:
        ```python
        from p8s import Model
        from p8s.storage import FileField

        class Document(Model, table=True):
            title: str
            file: str | None = FileField(
                upload_to="documents/",
                allowed_extensions=[".pdf", ".doc", ".docx"],
                max_size=10 * 1024 * 1024,  # 10MB
            )
        ```

    Args:
        upload_to: Subdirectory for uploads within the storage location.
        storage: Storage backend to use. Defaults to FileSystemStorage.
        max_size: Maximum file size in bytes. None for unlimited.
        allowed_extensions: List of allowed file extensions (with dots).
        description: Field description for documentation.
        **kwargs: Additional Field arguments.

    Returns:
        A SQLModel field configured for file storage.
    """
    return Field(
        default=None,
        max_length=500,
        description=description or "File path",
        json_schema_extra={
            "x-p8s-file-field": True,
            "x-p8s-upload-to": upload_to,
            "x-p8s-max-size": max_size,
            "x-p8s-allowed-extensions": allowed_extensions,
        },
        **kwargs,
    )


def ImageField(
    upload_to: str = "",
    storage: Storage | None = None,
    max_size: int | None = None,
    allowed_extensions: list[str] | None = None,
    width_field: str | None = None,
    height_field: str | None = None,
    description: str | None = None,
    **kwargs: Any,
) -> Any:
    """
    Create an image field for storing uploaded images.

    Similar to FileField but with image-specific features like
    automatic dimension detection and image validation.

    Example:
        ```python
        from p8s import Model
        from p8s.storage import ImageField

        class Product(Model, table=True):
            name: str
            image: str | None = ImageField(
                upload_to="products/images/",
                max_size=5 * 1024 * 1024,  # 5MB
            )
            image_width: int | None = None
            image_height: int | None = None
        ```

    Args:
        upload_to: Subdirectory for uploads within the storage location.
        storage: Storage backend to use. Defaults to FileSystemStorage.
        max_size: Maximum file size in bytes. None for unlimited.
        allowed_extensions: Allowed extensions. Defaults to common image formats.
        width_field: Field name to store image width.
        height_field: Field name to store image height.
        description: Field description for documentation.
        **kwargs: Additional Field arguments.

    Returns:
        A SQLModel field configured for image storage.
    """
    if allowed_extensions is None:
        allowed_extensions = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"]

    return Field(
        default=None,
        max_length=500,
        description=description or "Image path",
        json_schema_extra={
            "x-p8s-image-field": True,
            "x-p8s-upload-to": upload_to,
            "x-p8s-max-size": max_size,
            "x-p8s-allowed-extensions": allowed_extensions,
            "x-p8s-width-field": width_field,
            "x-p8s-height-field": height_field,
        },
        **kwargs,
    )


# ============================================================================
# File handling utilities
# ============================================================================


async def save_uploaded_file(
    content: bytes | BytesIO,
    filename: str,
    upload_to: str = "",
    storage: Storage | None = None,
    max_size: int | None = None,
    allowed_extensions: list[str] | None = None,
) -> str:
    """
    Save an uploaded file to storage.

    Args:
        content: File content as bytes or BytesIO
        filename: Original filename
        upload_to: Subdirectory for the upload
        storage: Storage backend (defaults to default storage)
        max_size: Maximum file size in bytes
        allowed_extensions: Allowed file extensions

    Returns:
        Path to the saved file

    Raises:
        ValueError: If file validation fails
    """
    from pathlib import Path as PathLib

    storage = storage or get_default_storage()

    # Convert bytes to BytesIO if needed
    if isinstance(content, bytes):
        content = BytesIO(content)

    # Validate file size
    content.seek(0, 2)  # Seek to end
    file_size = content.tell()
    content.seek(0)  # Reset to beginning

    if max_size and file_size > max_size:
        raise ValueError(
            f"File size ({file_size} bytes) exceeds maximum ({max_size} bytes)"
        )

    # Validate extension
    ext = PathLib(filename).suffix.lower()
    if allowed_extensions and ext not in allowed_extensions:
        raise ValueError(
            f"File extension '{ext}' not allowed. Allowed: {allowed_extensions}"
        )

    # Generate unique filename
    unique_name = storage.generate_filename(filename, upload_to)

    # Save file
    saved_path = storage.save(unique_name, content)

    return saved_path


async def delete_file(
    path: str,
    storage: Storage | None = None,
) -> bool:
    """
    Delete a file from storage.

    Args:
        path: File path to delete
        storage: Storage backend (defaults to default storage)

    Returns:
        True if deleted, False if not found
    """
    storage = storage or get_default_storage()
    return storage.delete(path)


def get_file_url(
    path: str,
    storage: Storage | None = None,
) -> str:
    """
    Get the URL for a stored file.

    Args:
        path: File path
        storage: Storage backend (defaults to default storage)

    Returns:
        URL to access the file
    """
    storage = storage or get_default_storage()
    return storage.url(path)


def get_image_dimensions(content: bytes | BytesIO) -> tuple[int, int] | None:
    """
    Get image dimensions.

    Args:
        content: Image content as bytes or BytesIO

    Returns:
        Tuple of (width, height) or None if not an image
    """
    try:
        from PIL import Image

        if isinstance(content, bytes):
            content = BytesIO(content)

        content.seek(0)
        with Image.open(content) as img:
            return img.size
    except ImportError:
        # Pillow not installed
        return None
    except Exception:
        return None
