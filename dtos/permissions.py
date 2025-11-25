from enum import StrEnum


class Role(StrEnum):
    """User roles for RBAC.

    ADMIN: Full control within their tenant (manage users, create notes).
    EDITOR: Can create and view notes within their tenant.
    VIEWER: Can only view notes within their tenant.
    """

    ADMIN = "ADMIN"
    EDITOR = "EDITOR"
    VIEWER = "VIEWER"
