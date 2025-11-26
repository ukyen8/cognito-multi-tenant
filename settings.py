from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings for the platform lambda environment."""

    region_name: str = Field(default="us-east-2", alias="AWS_REGION")
    log_level: str = Field(default="INFO")
    environment: str = Field(default="local", alias="ENVIRONMENT")

    user_pool_id: str = Field(default="", alias="USER_POOL_ID")
    app_client_id: str = Field(default="", alias="APP_CLIENT_ID")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


def get_settings() -> Settings:
    return Settings()
