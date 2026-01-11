"""
P8s Storage - File storage backends and field types.

Provides Django-style file handling with:
- FileField and ImageField for models
- Configurable storage backends (filesystem, S3)
- Automatic file handling on CRUD operations
"""

from p8s.storage.base import FileSystemStorage, Storage
from p8s.storage.fields import FileField, ImageField

__all__ = [
    # Storage backends
    "Storage",
    "FileSystemStorage",
    # Fields
    "FileField",
    "ImageField",
]
