"""
P8s Core Module - Application factory and configuration.
"""

from p8s.core.application import P8sApp
from p8s.core.routing import Router
from p8s.core.settings import Settings, get_settings

__all__ = [
    "P8sApp",
    "Settings",
    "get_settings",
    "Router",
]
