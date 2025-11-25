from fastapi import APIRouter, HTTPException, Depends
from http import HTTPStatus
from dtos.auth import UserClaims
from dtos.permissions import Role
from dtos.tenant import (
    TenantCreate,
    TenantResponse,
    UserCreate,
    UserResponse,
    TenantCreateRequest,
    UserCreateRequest,
)
from cognito import require_role, get_cognito_client
from settings import get_settings, Settings
from managers import TenantUserManager
from managers import get_tenant_user_manager
import logging
from mypy_boto3_cognito_idp.client import CognitoIdentityProviderClient

logger = logging.getLogger()
router = APIRouter()


@router.post(
    "/tenants",
    response_model=TenantResponse,
    status_code=HTTPStatus.CREATED,
    response_model_exclude_none=True,
    tags=["internal"],
    summary="[INTERNAL] Create a new tenant (ADMIN only)",
)
async def add_tenant(
    tenant: TenantCreateRequest,
    user: UserClaims = Depends(require_role([Role.ADMIN])),
    tenant_user_manager: TenantUserManager = Depends(get_tenant_user_manager),
) -> TenantResponse:
    """Create a new tenant. Only ADMIN can perform this action."""
    # TODO: Validate tenant name uniqueness
    tenant_create = TenantCreate(
        tenant_name=tenant.tenant_name,
    )
    tenant_response = tenant_user_manager.create_tenant(tenant_create)
    logger.info(
        f"Tenant {tenant_create.tenant_id} created by user {user.user_id}"
    )
    return tenant_response


@router.get(
    "/tenants",
    response_model=list[TenantResponse],
    status_code=HTTPStatus.OK,
    response_model_exclude_none=True,
    tags=["internal"],
    summary="[INTERNAL] List all tenants (ADMIN only)",
)
async def list_tenants(
    user: UserClaims = Depends(require_role([Role.ADMIN])),
    tenant_user_manager: TenantUserManager = Depends(get_tenant_user_manager),
) -> list[TenantResponse]:
    """List all tenants. Only ADMIN can perform this action."""
    tenants = tenant_user_manager.list_tenants()
    logger.info(f"User {user.user_id} listed all tenants.")
    return tenants


@router.post(
    "/tenants/{tenant_id}/user",
    response_model=UserResponse,
    status_code=HTTPStatus.CREATED,
    response_model_exclude_none=True,
    tags=["internal"],
    summary="[INTERNAL] Add a user to a tenant (ADMIN only)",
)
async def add_user_to_tenant(
    tenant_id: str,
    user_data: UserCreateRequest,
    user: UserClaims = Depends(require_role([Role.ADMIN])),
    settings: Settings = Depends(get_settings),
    tenant_user_manager: TenantUserManager = Depends(get_tenant_user_manager),
    client: CognitoIdentityProviderClient = Depends(get_cognito_client),
) -> UserResponse:
    """Add a user to a tenant and assign roles using Cognito.

    Only ADMIN can perform this action.
    """
    user_pool_id = settings.user_pool_id
    if not tenant_user_manager.tenant_exists(tenant_id):
        logger.info(f"Tenant {tenant_id} does not exist. Cannot add user.")
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Tenant not found."
        )

    try:
        client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=user_data.email,  # Use email as Cognito username
            UserAttributes=[
                {"Name": "email", "Value": user_data.email},
                # Mark email as verified for dev/test
                {"Name": "email_verified", "Value": "true"},
                # Associate tenant ID with the user
                {"Name": "custom:tenant_id", "Value": tenant_id},
            ],
            DesiredDeliveryMediums=["EMAIL"],
        )

        cognito_user_id = user_data.email

        # Set default password and make it permanent for dev/test
        client.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username=cognito_user_id,
            Password="P@ssword123",  # noqa: S106
            Permanent=True,
        )
        # Add user to the specified group/role in Cognito
        client.admin_add_user_to_group(
            UserPoolId=user_pool_id,
            Username=cognito_user_id,
            GroupName=user_data.role.value,
        )
        logger.info(
            f"User {cognito_user_id} created in tenant {tenant_id} with roles"
            f" {user_data.role} by {user.user_id} and default password set."
        )
    except client.exceptions.UsernameExistsException:
        logger.warning(f"User already exists: {user_data.email}")
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail="User already exists."
        ) from None
    except Exception as e:
        logger.exception(f"Failed to create user: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Failed to create user.",
        ) from e

    return tenant_user_manager.create_user(
        UserCreate(
            email=user_data.email,
            role=user_data.role,
        ),
        tenant_id=tenant_id,
    )
