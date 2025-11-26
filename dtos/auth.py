from pydantic import BaseModel, Field

from dtos.permissions import Role


class UserClaims(BaseModel):
    """Represents the claims extracted from a Cognito JWT token."""

    email: str | None = Field(None, description="The user's email address")
    cognito_groups: list[Role] = Field(
        default_factory=list,
        alias="cognito:groups",
        description="Cognito groups/roles for the user",
    )
    tenant_id: str | None = Field(
        None,
        description="The tenant ID associated with the user",
        validation_alias="custom:tenant_id",
    )
    user_id: str | None = Field(
        None,
        description="The unique user ID, if different from sub",
        validation_alias="sub",
    )

    class Config:
        populate_by_name = True


class TokenRequest(BaseModel):
    username: str = Field(..., description="The user's email address")
    password: str


class TokenResponse(BaseModel):
    id_token: str
    access_token: str
    refresh_token: str
