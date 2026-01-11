"""
P8s Auth Module - Authentication and authorization.
"""

from p8s.auth.decorators import (
    login_required,
    require_login,
    require_perm,
    require_perms,
    require_staff,
    require_superuser,
    staff_member_required,
    superuser_required,
    user_passes_test,
)
from p8s.auth.dependencies import (
    AdminUser,
    AuthenticatedUser,
    CurrentUser,
    get_current_user,
    require_admin,
    require_auth,
    require_permission,
    require_role,
)
from p8s.auth.models import User, UserCreate, UserRole, UserUpdate
from p8s.auth.permissions import (
    Group,
    Permission,
    create_model_permissions,
    get_permission_codename,
    permission_required,
)
from p8s.auth.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
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
