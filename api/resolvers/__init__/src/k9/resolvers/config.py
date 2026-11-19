import os
from functools import cache, cached_property

import boto3
from requests_aws4auth import AWS4Auth
from types_boto3_ssm import SSMClient

__all__ = [
    "settings",
]


class MissingSettingError(RuntimeError):
    def __init__(self, *keys: str):
        variables = ", ".join(keys)
        super().__init__(f"Missing required environment setting. Checked: {variables}")


class Settings:
    def aws_auth(self, session: boto3.Session) -> AWS4Auth:
        credentials = session.get_credentials()
        if credentials is None:
            raise MissingSettingError("AWS credentials")
        return AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            session.region_name,
            "es",
            session_token=credentials.token,
        )

    @cached_property
    def aws_region(self) -> str:
        options = ("APP_AWS_REGION", "AWS_REGION", "AWS_DEFAULT_REGION")
        for key in options:
            if value := os.getenv(key):
                return value
        raise MissingSettingError(*options)

    @cached_property
    def _ssm(self) -> SSMClient:
        return boto3.client("ssm", region_name=self.aws_region)

    @cache
    def getssm(self, key: str) -> str | None:
        if not (name := os.getenv(key)):
            return None
        param = self._ssm.get_parameter(Name=name, WithDecryption=True)["Parameter"]
        return param.get("Value")

    def __getattr__(self, key: str) -> str:
        key = key.upper()
        if value := (os.getenv(key) or self.getssm(f"{key}_PARAMETER")):
            return value
        raise MissingSettingError(key, f"{key}_PARAMETER")


settings = Settings()
