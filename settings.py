from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings for the platform lambda environment."""

    region_name: str = Field(default="us-east-2", alias="AWS_REGION")
    log_level: str = Field(default="INFO")
    environment: str = Field(default="local", alias="ENVIRONMENT")

    product_table_name: str
    product_table_pk: str = "pk"
    product_table_sk: str = "sk"
    tenant_user_table_name: str
    tenant_user_table_pk: str = "pk"
    tenant_user_table_sk: str = "sk"

    user_pool_id: str = Field(default="", alias="USER_POOL_ID")
    app_client_id: str = Field(default="", alias="APP_CLIENT_ID")

    upload_bucket_name: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


def get_settings() -> Settings:
    return Settings()
