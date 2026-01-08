"""
P8s Auth Module - Authentication and authorization.
"""

from p8s.auth.models import User, UserCreate, UserUpdate, UserRole
from p8s.auth.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from p8s.auth.dependencies import (
    get_current_user,
    require_auth,
    require_admin,
    require_role,
    require_permission,
    CurrentUser,
    AuthenticatedUser,
    AdminUser,
)
from p8s.auth.permissions import (
    Permission,
    Group,
    permission_required,
    get_permission_codename,
    create_model_permissions,
)
from p8s.auth.decorators import (
    login_required,
    staff_member_required,
    superuser_required,
    user_passes_test,
    require_login,
    require_staff,
    require_superuser,
    require_perm,
    require_perms,
)

__all__ = [
    # Models
    "User",
    "UserCreate",
    "UserUpdate",
    # Permissions
    "Permission",
    "Group",
    "permission_required",
    "get_permission_codename",
    "create_model_permissions",
    # Security
    "get_password_hash",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    # Dependencies
    "get_current_user",
    "require_auth",
]

