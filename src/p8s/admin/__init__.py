"""
P8s Admin Module - Auto-generated admin panel.
"""

from p8s.admin.actions import admin_action, register_action
from p8s.admin.inlines import StackedInline, TabularInline
from p8s.admin.registry import get_registered_models, register_model
from p8s.admin.router import create_admin_router
from p8s.admin.site import ModelAdmin, site

__all__ = [
    "create_admin_router",
    "register_model",
    "get_registered_models",
    "admin_action",
    "register_action",
    "TabularInline",
    "StackedInline",
    "site",
    "ModelAdmin",
]
