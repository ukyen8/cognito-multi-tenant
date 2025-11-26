from enum import StrEnum


class Role(StrEnum):
    """User roles for RBAC."""

    ADMIN = "ADMIN"
    EDITOR = "EDITOR"
    VIEWER = "VIEWER"

PERMISSION_SCORE = {
    Role.ADMIN: 3,
    Role.EDITOR: 2,
    Role.VIEWER: 1
}
