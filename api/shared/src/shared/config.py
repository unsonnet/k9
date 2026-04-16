import os
from functools import cached_property


class MissingSettingError(RuntimeError):
    def __init__(self, *keys: str):
        self.keys = keys
        joined = ", ".join(keys)
        super().__init__(f"Missing required environment setting. Checked: {joined}")


class Settings:
    def get(self, key: str, default: str | None = None) -> str | None:
        return os.getenv(key, default)

    def require(self, *keys: str) -> str:
        for key in keys:
            value = os.getenv(key)
            if value:
                return value
        raise MissingSettingError(*keys)

    @cached_property
    def aws_region(self) -> str:
        return self.require("AWS_REGION", "AWS_DEFAULT_REGION")

    @cached_property
    def cognito_client_id(self) -> str:
        return self.require("COGNITO_CLIENT_ID")

    @cached_property
    def cognito_client_secret(self) -> str:
        return self.require("COGNITO_CLIENT_SECRET")

    @cached_property
    def cognito_user_pool_id(self) -> str:
        return self.require("COGNITO_USER_POOL_ID")


settings = Settings()
