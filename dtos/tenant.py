import uuid
from typing import Self
from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from dtos.permissions import Role


class TenantCreateRequest(BaseModel):
    tenant_name: str = Field(..., description="Name of the tenant")


class TenantCreate(TenantCreateRequest):
    tenant_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for the tenant",
    )


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


class UserCreate(UserCreateRequest):
    user_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for the user",
    )


class UserResponse(BaseModel):
    """Represent the response for a created user in a tenant."""

    user_id: str
    email: str
    role: str
    tenant_id: str


class TenantRecord(BaseModel):
    """Represent a tenant record in DynamoDB."""

    pk: str
    sk: str
    tenant_id: str
    tenant_name: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime | None = None


class UserRecord(BaseModel):
    """Represent a user record in DynamoDB."""

    pk: str
    sk: str
    user_id: str
    username: str
    email: str
    role: str
    tenant_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime | None = None
