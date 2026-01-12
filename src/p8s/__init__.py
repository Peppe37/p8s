"""
P8s (Prometheus) - Forge AI-native, full-stack applications with the fire of the gods.

P8s is an opinionated, batteries-included framework that fuses the architecture
and DX of Django with the performance and async nature of FastAPI, plus first-class
AI/LLM integration and a native React frontend.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("p8s")
except PackageNotFoundError:
    __version__ = "unknown"

__author__ = "Giuseppe Lapietra"

# Core exports
# Auth exports
from p8s.auth.permissions import Group, Permission
from p8s.core.application import P8sApp
from p8s.core.settings import Settings, get_settings
from p8s.db.base import Model

# DB Fields
from p8s.db.fields import (
    BooleanField,
    CharField,
    DateField,
    DateTimeField,
    DecimalField,
    EmailField,
    FloatField,
    ForeignKey,
    IntegerField,
    JSONField,
    ManyToManyField,
    OneToOneField,
    TextField,
    URLField,
)
from p8s.db.session import get_session
from p8s.db.signals import Signal, receiver

# Storage exports
from p8s.storage import FileField, ImageField

# AI exports (optional)
try:
    from p8s.ai.fields import AIField, VectorField
except ImportError:
    AIField = None  # type: ignore
    VectorField = None  # type: ignore

__all__ = [
    # Core
    "P8sApp",
    "Settings",
    "get_settings",
    # Database
    "Model",
    "get_session",
    # Signals
    "Signal",
    "receiver",
    # Auth
    "Permission",
    "Group",
    # Storage
    "FileField",
    "ImageField",
    # Fields
    "CharField",
    "TextField",
    "BooleanField",
    "IntegerField",
    "FloatField",
    "DecimalField",
    "DateField",
    "DateTimeField",
    "JSONField",
    "EmailField",
    "URLField",
    "ForeignKey",
    "ManyToManyField",
    "OneToOneField",
    # AI (optional)
    "AIField",
    "VectorField",
]

# Convenience alias
models = type("ModelsModule", (), {"Model": Model})()
