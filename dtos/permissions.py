from enum import StrEnum


class Role(StrEnum):
    """User roles for RBAC."""

    ADMIN = "ADMIN"
    EDITOR = "EDITOR"
    VIEWER = "VIEWER"

