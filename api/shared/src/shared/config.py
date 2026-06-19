import os
from functools import cached_property

import boto3
from requests_aws4auth import AWS4Auth
from types_boto3_ssm import SSMClient


class MissingSettingError(RuntimeError):
    def __init__(self, *keys: str):
        super().__init__(
            f"Missing required environment setting. Checked: {', '.join(keys)}"
        )
        self.keys = keys


class Settings:
    def get(self, key: str, default: str | None = None) -> str | None:
        return os.getenv(key, default)

    def require(self, *keys: str) -> str:
        for key in keys:
            if value := os.getenv(key):
                return value
        raise MissingSettingError(*keys)

    def from_parameter(self, key: str) -> str | None:
        if not (name := os.getenv(key)):
            return None
        return self._ssm.get_parameter(Name=name, WithDecryption=True)["Parameter"].get(
            "Value"
        )

    def env_or_parameter(self, key: str) -> str:
        if value := self.get(key) or self.from_parameter(f"{key}_PARAMETER"):
            return value
        raise MissingSettingError(key, f"{key}_PARAMETER")

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
        return self.require("APP_AWS_REGION", "AWS_REGION", "AWS_DEFAULT_REGION")

    @cached_property
    def _ssm(self) -> SSMClient:
        return boto3.client("ssm", region_name=self.aws_region)

    @cached_property
    def cognito_client_id(self) -> str:
        return self.env_or_parameter("COGNITO_CLIENT_ID")

    @cached_property
    def cognito_client_secret(self) -> str:
        return self.env_or_parameter("COGNITO_CLIENT_SECRET")

    @cached_property
    def cognito_user_pool_id(self) -> str:
        return self.env_or_parameter("COGNITO_USER_POOL_ID")

    @cached_property
    def dynamodb_table(self) -> str:
        return self.env_or_parameter("DYNAMODB_TABLE")

    @cached_property
    def s3_bucket(self) -> str:
        return self.env_or_parameter("S3_BUCKET")

    @cached_property
    def opensearch_endpoint(self) -> str:
        return self.env_or_parameter("OPENSEARCH_ENDPOINT")

    @cached_property
    def opensearch_index(self) -> str:
        return self.env_or_parameter("OPENSEARCH_INDEX")


settings = Settings()
