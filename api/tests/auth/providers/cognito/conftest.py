import auth.providers.cognito as cognito
import boto3
import pytest


@pytest.fixture(autouse=True)
def aws_env(monkeypatch: pytest.MonkeyPatch):
    """
    Prevent boto3 from attempting to discover real AWS credentials.

    These tests use botocore Stubber, so no real AWS calls are made, but boto3
    still needs credentials available when constructing/signing requests.
    """
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")


@pytest.fixture
def cognito_client():
    return boto3.client("cognito-idp", region_name="us-east-1")


@pytest.fixture
def provider(monkeypatch: pytest.MonkeyPatch, cognito_client):
    monkeypatch.setattr(
        cognito.boto3,
        "client",
        lambda service_name, region_name=None: cognito_client,
    )

    return cognito.CognitoAuthProvider(
        region="us-east-1",
        client_id="client-id",
        client_secret="client-secret-value-1234",
    )
