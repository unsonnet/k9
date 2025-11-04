#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


# ──────────────────────────────────────────────────────────────────────────────
# S3
# ──────────────────────────────────────────────────────────────────────────────


@runtime_checkable
class _S3Client(Protocol):
    exceptions: Any

    def put_object(
        self,
        *,
        Bucket: str,
        Key: str,
        Body: bytes,
        ContentType: str | None = None,
    ) -> dict[str, Any]: ...

    def get_object(
        self,
        *,
        Bucket: str,
        Key: str,
    ) -> dict[str, Any]: ...

    def delete_object(
        self,
        *,
        Bucket: str,
        Key: str,
    ) -> dict[str, Any]: ...

    def generate_presigned_url(
        self,
        ClientMethod: str,
        Params: dict[str, Any],
        ExpiresIn: int,
    ) -> str: ...


# ──────────────────────────────────────────────────────────────────────────────
# DynamoDB
# ──────────────────────────────────────────────────────────────────────────────


@runtime_checkable
class _DynamoTable(Protocol):
    def get_item(self, *, Key: dict[str, Any]) -> dict[str, Any]: ...
    def put_item(
        self, *, Item: dict[str, Any], ConditionExpression: str
    ) -> dict[str, Any]: ...
    def delete_item(
        self, *, Key: dict[str, Any], ConditionExpression: str
    ) -> dict[str, Any]: ...


@runtime_checkable
class _DynamoClient(Protocol):
    exceptions: Any


@runtime_checkable
class _DynamoResource(Protocol):
    def Table(self, name: str) -> _DynamoTable: ...


# ──────────────────────────────────────────────────────────────────────────────
# Cognito
# ──────────────────────────────────────────────────────────────────────────────


@runtime_checkable
class _CognitoIdP(Protocol):
    exceptions: Any

    # Authentication flows
    def initiate_auth(
        self, *, AuthFlow: str, ClientId: str, AuthParameters: dict[str, str]
    ) -> dict[str, Any]: ...
    def respond_to_auth_challenge(
        self,
        *,
        ClientId: str,
        ChallengeName: str,
        ChallengeResponses: dict[str, str],
        Session: str,
    ) -> dict[str, Any]: ...
    def revoke_token(
        self, *, Token: str, ClientId: str, ClientSecret: str
    ) -> dict[str, Any]: ...

    # Password reset
    def forgot_password(
        self, *, ClientId: str, Username: str, SecretHash: str
    ) -> dict[str, Any]: ...

    # Access tokens → identity data
    def get_user(self, *, AccessToken: str) -> dict[str, Any]: ...

    # User management (admin)
    def admin_get_user(self, *, UserPoolId: str, Username: str) -> dict[str, Any]: ...
    def admin_create_user(
        self,
        *,
        UserPoolId: str,
        Username: str,
        UserAttributes: list[dict[str, str]],
        TemporaryPassword: str,
        MessageAction: str,
    ) -> dict[str, Any]: ...
    def admin_update_user_attributes(
        self, *, UserPoolId: str, Username: str, UserAttributes: list[dict[str, str]]
    ) -> dict[str, Any]: ...
    def admin_delete_user(
        self, *, UserPoolId: str, Username: str
    ) -> dict[str, Any]: ...
    def admin_set_user_password(
        self, *, UserPoolId: str, Username: str, Password: str, Permanent: bool
    ) -> dict[str, Any]: ...

    # Listing / paging users
    def list_users(
        self,
        *,
        UserPoolId: str,
        Filter: str | None = None,
        Limit: int | None = None,
        PaginationToken: str | None = None,
    ) -> dict[str, Any]: ...
    def describe_user_pool(self, *, UserPoolId: str) -> dict[str, Any]: ...
