"""
P8s Frontend Module - React integration and TypeScript generation.
"""

from p8s.frontend.types import generate_typescript_types
from p8s.frontend.utils import get_vite_config

__all__ = [
    "generate_typescript_types",
    "get_vite_config",
]
