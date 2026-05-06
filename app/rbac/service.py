"""Compute effective permissions for a user: role defaults + user_permissions."""
from app.models.user import User
from app.rbac.permissions import ROLE_DEFAULTS


def get_effective_permissions(user: User) -> set[str]:
    """
    Returns the full set of permission codes for the user:
      role default codes  ∪  explicit user_permissions codes
    """
    role_codes = ROLE_DEFAULTS.get(user.role.value, set())
    extra_codes = {
        up.permission.code
        for up in (user.user_permissions or [])
        if up.permission is not None
    }
    return role_codes | extra_codes


def has_permission(user: User, code: str) -> bool:
    return code in get_effective_permissions(user)
