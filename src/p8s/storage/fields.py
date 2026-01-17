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


def resize_image(
    content: bytes | BytesIO,
    max_width: int | None = None,
    max_height: int | None = None,
    max_size: tuple[int, int] | None = None,
    quality: int = 85,
    format: str | None = None,
) -> BytesIO:
    """
    Resize an image to fit within maximum dimensions.

    The image is resized proportionally to fit within the specified
    maximum dimensions while maintaining aspect ratio.

    Example:
        ```python
        from p8s.storage.fields import resize_image

        with open("large_photo.jpg", "rb") as f:
            resized = resize_image(f.read(), max_size=(800, 600))
        ```

    Args:
        content: Image content as bytes or BytesIO
        max_width: Maximum width in pixels
        max_height: Maximum height in pixels
        max_size: Tuple of (max_width, max_height) - alternative to separate params
        quality: JPEG quality (1-100), default 85
        format: Output format ('JPEG', 'PNG', etc). Auto-detected if None.

    Returns:
        BytesIO with resized image content

    Raises:
        ImportError: If Pillow is not installed
        ValueError: If image cannot be processed
    """
    try:
        from PIL import Image
    except ImportError:
        raise ImportError(
            "Pillow is required for image resize. Install with: pip install Pillow"
        )

    if isinstance(content, bytes):
        content = BytesIO(content)

    content.seek(0)

    try:
        with Image.open(content) as img:
            original_format = img.format or "JPEG"
            output_format = format or original_format

            # Handle max_size tuple
            if max_size:
                max_width = max_size[0]
                max_height = max_size[1]

            # If no max dimensions specified, return original
            if not max_width and not max_height:
                content.seek(0)
                return content

            width, height = img.size

            # Calculate new size maintaining aspect ratio
            if max_width and max_height:
                ratio = min(max_width / width, max_height / height)
            elif max_width:
                ratio = max_width / width
            else:
                ratio = max_height / height

            # Only resize if image is larger than max
            if ratio < 1:
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Convert RGBA to RGB for JPEG
            if output_format.upper() == "JPEG" and img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            output = BytesIO()
            img.save(output, format=output_format, quality=quality, optimize=True)
            output.seek(0)
            return output

    except Exception as e:
        raise ValueError(f"Failed to resize image: {e}")


# MIME type magic bytes signatures
MIME_SIGNATURES = {
    # Images
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
    b"RIFF": "image/webp",  # WebP starts with RIFF...WEBP
    b"<svg": "image/svg+xml",
    b"<?xml": "image/svg+xml",  # SVG can start with XML declaration
    # Documents
    b"%PDF": "application/pdf",
    b"PK\x03\x04": "application/zip",  # Also docx, xlsx, etc.
    # Archives
    b"\x1f\x8b": "application/gzip",
    b"Rar!": "application/x-rar-compressed",
}


def validate_mime_type(
    content: bytes | BytesIO,
    allowed_types: list[str] | None = None,
) -> str | None:
    """
    Detect and validate MIME type from file content.

    Uses magic bytes (file signatures) to detect the actual file type,
    regardless of file extension. This provides security against
    disguised file uploads.

    Example:
        ```python
        from p8s.storage.fields import validate_mime_type

        with open("upload.jpg", "rb") as f:
            mime = validate_mime_type(f.read(), allowed_types=["image/jpeg", "image/png"])
            if mime is None:
                raise ValueError("Invalid file type")
        ```

    Args:
        content: File content as bytes or BytesIO
        allowed_types: List of allowed MIME types. If None, just detect.

    Returns:
        Detected MIME type if valid, None if invalid or not allowed

    Raises:
        ValueError: If file type is not allowed
    """
    if isinstance(content, BytesIO):
        content.seek(0)
        header = content.read(32)
        content.seek(0)
    else:
        header = content[:32]

    detected_mime = None

    # Check against known signatures
    for signature, mime_type in MIME_SIGNATURES.items():
        if header.startswith(signature):
            detected_mime = mime_type
            break

    # Special case for WebP (RIFF....WEBP)
    if header[:4] == b"RIFF" and len(header) >= 12 and header[8:12] == b"WEBP":
        detected_mime = "image/webp"

    # If no allowed_types specified, just return detected type
    if allowed_types is None:
        return detected_mime

    # Validate against allowed types
    if detected_mime and detected_mime in allowed_types:
        return detected_mime

    # If detection failed but we have allowed types, raise error
    if detected_mime:
        raise ValueError(
            f"File type '{detected_mime}' not allowed. Allowed: {allowed_types}"
        )
    else:
        raise ValueError(f"Unknown file type. Allowed: {allowed_types}")
