from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Literal, Optional, overload

import boto3

from utils.aws import _CognitoIdP, _S3Client, _DynamoClient, _DynamoResource


@dataclass(frozen=True)
class Settings:
    platform: str = os.getenv("PLATFORM", "local")  # "local" | "aws"
    aws_region: str = os.getenv(
        "AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    )

    # Data stores
    reports_table: str = os.getenv("REPORTS_TABLE", "k9_reports")
    products_table: str = os.getenv("PRODUCTS_TABLE", "k9_products")
    images_bucket: str = os.getenv("IMAGES_BUCKET", "k9-images")

    # Search
    opensearch_endpoint: Optional[str] = os.getenv("OPENSEARCH_ENDPOINT")
    opensearch_index: str = os.getenv("OPENSEARCH_INDEX", "products")

    # Auth/JWT
    jwt_secret: str = os.getenv("JWT_SECRET", "change-me-in-prod")
    jwt_issuer: str = os.getenv("JWT_ISSUER", "k9-api")
    jwt_audience: str = os.getenv("JWT_AUDIENCE", "k9-clients")
    access_token_ttl: int = int(os.getenv("ACCESS_TOKEN_TTL", "900"))  # seconds
    refresh_token_ttl: int = int(os.getenv("REFRESH_TOKEN_TTL", "1209600"))  # 14 days

    # Auth mode: local HS256 or cognito (RS256)
    cognito_user_pool_id: Optional[str] = os.getenv("COGNITO_USER_POOL_ID")
    cognito_client_id: Optional[str] = os.getenv("COGNITO_CLIENT_ID")
    cognito_client_secret: Optional[str] = os.getenv("COGNITO_CLIENT_SECRET")

    # Roles
    admin_role: str = os.getenv("ADMIN_ROLE", "admin")


_settings = Settings()


def settings() -> Settings:
    return _settings


# -------- boto3_client --------


@overload
def boto3_client(service: Literal["cognito-idp"]) -> _CognitoIdP: ...
@overload
def boto3_client(service: Literal["dynamodb"]) -> _DynamoClient: ...
@overload
def boto3_client(service: Literal["s3"]) -> _S3Client: ...
@overload
def boto3_client(service: str) -> Any: ...


def boto3_client(service: str) -> Any:
    return boto3.client(service, region_name=settings().aws_region)  # type: ignore[call-overload]


# -------- boto3_resource --------


@overload
def boto3_resource(service: Literal["dynamodb"]) -> _DynamoResource: ...
@overload
def boto3_resource(service: str) -> Any: ...


def boto3_resource(service: str) -> Any:
    return boto3.resource(service, region_name=settings().aws_region)  # type: ignore[call-overload]
