import uuid

from fastapi import APIRouter, HTTPException, Depends
from http import HTTPStatus
from dtos.tenant import TenantResponse, UserCreateRequest, UserResponse
from cognito import get_cognito_client
from settings import get_settings, Settings
import logging
from mypy_boto3_cognito_idp.client import CognitoIdentityProviderClient

logger = logging.getLogger()
router = APIRouter()


TENANT_DB = {}


@router.post(
    "/tenants",
    response_model=TenantResponse,
    status_code=HTTPStatus.CREATED,
    response_model_exclude_none=True,
    tags=["internal"],
)
async def add_tenant(tenant_name: str) -> TenantResponse:
    """Create a new tenant."""
    tenant_id = str(uuid.uuid4())
    tenant_response = TenantResponse(
        tenant_id=tenant_id,
        tenant_name=tenant_name,
    )
    TENANT_DB[tenant_id] = tenant_name
    return tenant_response


@router.get(
    "/tenants",
    response_model=list[TenantResponse],
    status_code=HTTPStatus.OK,
    response_model_exclude_none=True,
    tags=["internal"],
)
async def list_tenants() -> list[TenantResponse]:
    """List all tenants."""
    return [
        TenantResponse(tenant_id=k, tenant_name=v)
        for k, v in TENANT_DB.items()
    ]


@router.post(
    "/tenants/{tenant_id}/user",
    status_code=HTTPStatus.CREATED,
    response_model_exclude_none=True,
    tags=["internal"],
)
async def add_user_to_tenant(
    tenant_id: str,
    user_data: UserCreateRequest,
    settings: Settings = Depends(get_settings),
    client: CognitoIdentityProviderClient = Depends(get_cognito_client),
) -> UserResponse:
    """Add a user to a tenant and assign roles using Cognito."""
    user_pool_id = settings.user_pool_id
    if tenant_id not in TENANT_DB:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Tenant not found."
        )

    try:
        response = client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=user_data.email,
            UserAttributes=[
                {"Name": "email", "Value": user_data.email},
                {"Name": "email_verified", "Value": "true"},
                # Associate tenant ID with the user
                {"Name": "custom:tenant_id", "Value": tenant_id},
            ],
            DesiredDeliveryMediums=["EMAIL"],
        )

        cognito_user_id = user_data.email

        # Set default password and make it permanent for testing
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
            GroupName=user_data.role,
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

    for attr in response["User"]["Attributes"]:
        if attr["Name"] == "sub":
            user_id = attr["Value"]

    return UserResponse(
        user_id=user_id,
        email=user_data.email,
        role=user_data.role,
        tenant_id=tenant_id,
    )
