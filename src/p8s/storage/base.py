"""
P8s Storage Backends - Pluggable file storage system.

Provides:
- Abstract Storage base class
- FileSystemStorage for local files
- S3Storage for AWS S3 (optional)
"""

import shutil
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, BinaryIO
from uuid import uuid4

from p8s.core.settings import get_settings


class Storage(ABC):
    """
    Abstract base class for file storage backends.

    Subclass this to implement custom storage backends (S3, GCS, etc.).

    Example:
        ```python
        class MyStorage(Storage):
            def save(self, name: str, content: BinaryIO) -> str:
                # Custom implementation
                ...
        ```
    """

    @abstractmethod
    def save(self, name: str, content: BinaryIO, **kwargs: Any) -> str:
        """
        Save a file and return its name/path.

        Args:
            name: Desired file name (may be modified for uniqueness)
            content: File content as binary stream
            **kwargs: Additional storage-specific options

        Returns:
            The actual name/path where the file was saved
        """
        pass

    @abstractmethod
    def delete(self, name: str) -> bool:
        """
        Delete a file.

        Args:
            name: File name/path to delete

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    def exists(self, name: str) -> bool:
        """
        Check if a file exists.

        Args:
            name: File name/path to check

        Returns:
            True if file exists
        """
        pass

    @abstractmethod
    def url(self, name: str) -> str:
        """
        Get the URL to access a file.

        Args:
            name: File name/path

        Returns:
            URL string
        """
        pass

    @abstractmethod
    def size(self, name: str) -> int:
        """
        Get file size in bytes.

        Args:
            name: File name/path

        Returns:
            File size in bytes
        """
        pass

    def generate_filename(self, name: str, upload_to: str = "") -> str:
        """
        Generate a unique filename.

        Args:
            name: Original filename
            upload_to: Upload directory

        Returns:
            Unique filename with path
        """
        # Get file extension
        ext = Path(name).suffix.lower()

        # Generate unique name with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid4().hex[:8]
        new_name = f"{timestamp}_{unique_id}{ext}"

        if upload_to:
            return f"{upload_to.rstrip('/')}/{new_name}"
        return new_name


class FileSystemStorage(Storage):
    """
    Storage backend for local filesystem.

    Stores files in a configurable directory, defaulting to
    the `media/` directory in the project root.

    Example:
        ```python
        storage = FileSystemStorage()
        path = storage.save("document.pdf", file_content)
        url = storage.url(path)  # "/media/document.pdf"
        ```
    """

    def __init__(
        self,
        location: str | Path | None = None,
        base_url: str = "/media/",
    ) -> None:
        """
        Initialize filesystem storage.

        Args:
            location: Root directory for file storage.
                     Defaults to settings.base_dir / "media"
            base_url: Base URL for file access. Defaults to "/media/"
        """
        if location is None:
            settings = get_settings()
            self.location = Path(settings.base_dir) / "media"
        else:
            self.location = Path(location)

        self.base_url = base_url.rstrip("/") + "/"

        # Create directory if it doesn't exist
        self.location.mkdir(parents=True, exist_ok=True)

    def _path(self, name: str) -> Path:
        """Get full filesystem path for a file."""
        return self.location / name

    def save(self, name: str, content: BinaryIO, **kwargs: Any) -> str:
        """
        Save a file to the filesystem.

        Args:
            name: File name (can include subdirectory path)
            content: File content as binary stream
            **kwargs: Additional options (unused)

        Returns:
            The path where the file was saved (relative to location)
        """
        full_path = self._path(name)

        # Create subdirectories if needed
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Handle uniqueness if file exists
        if full_path.exists():
            # Add unique suffix
            stem = full_path.stem
            suffix = full_path.suffix
            unique_id = uuid4().hex[:8]
            name = f"{full_path.parent.relative_to(self.location)}/{stem}_{unique_id}{suffix}"
            full_path = self._path(name)

        # Write file
        with open(full_path, "wb") as f:
            shutil.copyfileobj(content, f)

        return name

    def delete(self, name: str) -> bool:
        """
        Delete a file from the filesystem.

        Args:
            name: File path relative to storage location

        Returns:
            True if deleted, False if not found
        """
        full_path = self._path(name)

        if full_path.exists() and full_path.is_file():
            full_path.unlink()
            return True
        return False

    def exists(self, name: str) -> bool:
        """
        Check if a file exists.

        Args:
            name: File path relative to storage location

        Returns:
            True if file exists
        """
        return self._path(name).exists()

    def url(self, name: str) -> str:
        """
        Get the URL to access a file.

        Args:
            name: File path relative to storage location

        Returns:
            URL string (e.g., "/media/uploads/file.pdf")
        """
        return f"{self.base_url}{name}"

    def size(self, name: str) -> int:
        """
        Get file size in bytes.

        Args:
            name: File path relative to storage location

        Returns:
            File size in bytes

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        full_path = self._path(name)
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {name}")
        return full_path.stat().st_size

    def listdir(self, path: str = "") -> tuple[list[str], list[str]]:
        """
        List contents of a directory.

        Args:
            path: Directory path relative to storage location

        Returns:
            Tuple of (directories, files)
        """
        full_path = self._path(path) if path else self.location

        directories = []
        files = []

        if full_path.exists() and full_path.is_dir():
            for item in full_path.iterdir():
                if item.is_dir():
                    directories.append(item.name)
                else:
                    files.append(item.name)

        return directories, files


# Default storage instance
_default_storage: Storage | None = None


def get_default_storage() -> Storage:
    """
    Get the default storage backend.

    Returns:
        Storage instance (FileSystemStorage by default)
    """
    global _default_storage

    if _default_storage is None:
        _default_storage = FileSystemStorage()

    return _default_storage


def set_default_storage(storage: Storage) -> None:
    """
    Set the default storage backend.

    Args:
        storage: Storage instance to use as default
    """
    global _default_storage
    _default_storage = storage
