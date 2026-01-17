"""
P8s Storage - File storage backends and field types.

Provides Django-style file handling with:
- FileField and ImageField for models
- Configurable storage backends (filesystem, S3, GCS)
- Automatic file handling on CRUD operations
"""

from p8s.storage.base import (
    FileSystemStorage,
    Storage,
    get_default_storage,
    set_default_storage,
)
from p8s.storage.fields import FileField, ImageField


# Lazy imports for cloud storage (require additional dependencies)
def __getattr__(name: str):
    if name == "S3Storage":
        from p8s.storage.s3 import S3Storage

        return S3Storage
    if name == "GCSStorage":
        from p8s.storage.s3 import GCSStorage

        return GCSStorage
    raise AttributeError(f"module 'p8s.storage' has no attribute '{name}'")


__all__ = [
    # Storage backends
    "Storage",
    "FileSystemStorage",
    "S3Storage",
    "GCSStorage",
    # Functions
    "get_default_storage",
    "set_default_storage",
    # Fields
    "FileField",
    "ImageField",
]
