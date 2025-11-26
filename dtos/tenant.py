from typing import Self

from pydantic import BaseModel, Field, model_validator

from dtos.permissions import Role


class TenantResponse(BaseModel):
    """Represent the response for a created tenant."""

    tenant_id: str
    tenant_name: str


class UserCreateRequest(BaseModel):
    email: str = Field(..., description="Email address for the new user")
    role: Role = Field(..., description="Roles for the new user")

    @model_validator(mode="after")
    def validate_role(self) -> Self:
        if self.role not in [Role.ADMIN, Role.VIEWER, Role.EDITOR]:
            raise ValueError(
                f"Invalid role: {self.role}. Allowed roles are: {Role.ADMIN}, {Role.VIEWER}, {Role.EDITOR}."  # noqa: E501
            )
        return self


class UserResponse(BaseModel):
    """Represent the response for a created user in a tenant."""

    user_id: str
    email: str
    role: str
    tenant_id: str
