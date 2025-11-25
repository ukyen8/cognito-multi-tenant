from dataclasses import dataclass

from fastapi import Depends
from dtos.tenant import (
    TenantCreate,
    TenantResponse,
    UserCreate,
    UserResponse,
    TenantRecord,
    UserRecord,
)
from storage import DynamoDBStore

from settings import Settings, get_settings


@dataclass()
class TenantUserManager:
    tenant_user_store: DynamoDBStore

    def create_tenant(self, tenant: TenantCreate) -> TenantResponse:
        """Create a new tenant and store in DynamoDB using TenantRecord."""
        record = TenantRecord(
            pk=f"TENANT#{tenant.tenant_id}",
            sk="METADATA",
            tenant_id=tenant.tenant_id,
            tenant_name=tenant.tenant_name,
        )
        self.tenant_user_store.put_item(record.model_dump(mode="json"))
        return TenantResponse(
            tenant_id=tenant.tenant_id, tenant_name=tenant.tenant_name
        )

    def list_tenants(self) -> list[TenantResponse]:
        items = self.tenant_user_store.scan_by_pk_prefix(
            pk_prefix="TENANT#",
            sk="METADATA",
        )
        return [
            TenantResponse(
                tenant_id=item["tenant_id"],
                tenant_name=item["tenant_name"],
            )
            for item in items
        ]

    def create_user(self, user: UserCreate, tenant_id: str) -> UserResponse:
        """Create a new user for a tenant."""
        record = UserRecord(
            pk=f"TENANT#{tenant_id}",
            sk=f"USER#{user.user_id}",
            user_id=user.user_id,
            username=user.email,
            email=user.email,
            role=user.role,
            tenant_id=tenant_id,
        )
        self.tenant_user_store.put_item(record.model_dump(mode="json"))
        return UserResponse(
            user_id=user.user_id,
            email=user.email,
            role=user.role,
            tenant_id=tenant_id,
        )

    def tenant_exists(self, tenant_id: str) -> bool:
        """Check if a tenant exists in DynamoDB."""
        item = self.tenant_user_store.get_item(
            f"TENANT#{tenant_id}", "METADATA"
        )
        return item is not None

    def get_users_by_tenant(self, tenant_id: str) -> list[UserResponse]:
        """Get all users for a specific tenant."""
        items = self.tenant_user_store.query_items(
            pk=f"TENANT#{tenant_id}",
        )
        return [
            UserResponse(
                user_id=item["user_id"],
                email=item["email"],
                role=item["role"],
                tenant_id=tenant_id,
            )
            for item in items
            if item["sk"].startswith("USER#")
        ]



def get_tenant_user_manager(
    settings: Settings = Depends(get_settings),
) -> TenantUserManager:
    """Dependency provider for TenantUserManager."""
    store = DynamoDBStore(
        table_name=settings.tenant_user_table_name,
        region_name=settings.region_name,
        part_key_name=settings.tenant_user_table_pk,
        sort_key_name=settings.tenant_user_table_sk,
        endpoint_url="http://localhost:8000"
        if settings.environment == "local"
        else None,
    )
    return TenantUserManager(tenant_user_store=store)
