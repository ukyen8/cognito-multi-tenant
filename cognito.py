from collections.abc import Callable

import boto3
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import requests
import logging

from dtos.permissions import Role
from settings import get_settings, Settings
from dtos.auth import UserClaims
from mypy_boto3_cognito_idp.client import CognitoIdentityProviderClient

_jwks_cache = {}


def get_cognito_issuer(settings: Settings) -> str:
    """Return the Cognito issuer URL for the current settings."""
    if settings.environment == "local":
        return f"http://0.0.0.0:9229/{settings.user_pool_id}"
    return f"https://cognito-idp.{settings.region_name}.amazonaws.com/{settings.user_pool_id}"


def get_jwks_url(settings: Settings) -> str:
    """Return the JWKS URL for the current settings."""
    return f"{get_cognito_issuer(settings)}/.well-known/jwks.json"


def get_jwks(settings: Settings) -> dict:
    """Fetch and cache JWKS for the given settings."""
    cache_key = (settings.region_name, settings.user_pool_id)
    if cache_key not in _jwks_cache:
        _jwks_cache[cache_key] = requests.get(get_jwks_url(settings)).json()  # noqa: S113
    return _jwks_cache[cache_key]


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(HTTPBearer()),
    settings: Settings = Depends(get_settings),
) -> UserClaims:
    """Validate JWT and return user claims as a UserClaims DTO."""
    token = credentials.credentials
    try:
        jwks = get_jwks(settings)
        claims = jwt.decode(
            token,
            jwks,
            options={"verify_aud": False},
            issuer=get_cognito_issuer(settings),
            algorithms=["RS256"],
        )
        return UserClaims.model_validate(claims)
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid token") from e


ROLES = {"admin", "editor", "viewer"}


def require_role(
    required_roles: list[Role],
) -> Callable[[UserClaims], UserClaims]:
    """Require user to have at least one of the specified roles.

    Args:
        required_roles: List of allowed Role enum values.

    Returns:
        Dependency function for FastAPI.

    """

    def role_checker(
        user: UserClaims = Depends(get_current_user),
    ) -> UserClaims:
        user_groups = user.cognito_groups or []
        allowed = any(role.value in user_groups for role in required_roles)
        if not allowed:
            logging.warning(
                f"User {user.user_id} lacks required roles: {[r.value for r in required_roles]}"  # noqa: E501
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return role_checker


def get_cognito_client(
    settings: Settings = Depends(get_settings),
) -> CognitoIdentityProviderClient:
    return boto3.client(
        "cognito-idp",
        region_name=settings.region_name,
        endpoint_url="http://localhost:9229"
        if settings.environment == "local"
        else None,
    )
