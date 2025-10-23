from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional

import boto3


@dataclass(frozen=True)
class Settings:
    stage: str = os.getenv("STAGE", "dev")  # "dev" | "prod"
    aws_region: str = os.getenv(
        "AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    )

    # Data stores
    products_table: str = os.getenv("PRODUCTS_TABLE", "k9_products")
    users_table: str = os.getenv("USERS_TABLE", "k9_users")
    reports_table: str = os.getenv("REPORTS_TABLE", "k9_reports")
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


def boto3_resource(name: str) -> Any:
    # Return Any to avoid strict overload typing issues at call sites
    return boto3.resource(name, region_name=settings().aws_region)  # type: ignore[call-overload]


def boto3_client(name: str) -> Any:
    return boto3.client(name, region_name=settings().aws_region)  # type: ignore[call-overload]
