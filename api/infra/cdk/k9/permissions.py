from collections.abc import Mapping, Sequence

from aws_cdk import ArnFormat, Stack
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_ssm as ssm
from constructs import Construct

from .config import Environment, StageName
from .manifest import Grant


def _parameter_value(scope: Construct, environment: Mapping[str, str], key: str) -> str:
    try:
        name = environment[key]
    except KeyError as exc:
        raise ValueError(f"Missing environment variable {key} for IAM alias") from exc
    return ssm.StringParameter.value_for_string_parameter(scope, name)


def resolve_resources(
    scope: Construct,
    stage: StageName,
    environment: Environment,
    resources: Sequence[str],
) -> list[str]:
    stack = Stack.of(scope)
    resolved: list[str] = []
    for resource in resources:
        if resource == "cognito-user-pool":
            pool = _parameter_value(
                scope, environment, "COGNITO_USER_POOL_ID_PARAMETER"
            )
            resolved.append(
                stack.format_arn(
                    service="cognito-idp", resource="userpool", resource_name=pool
                )
            )
        elif resource == "s3-bucket":
            bucket = _parameter_value(scope, environment, "S3_BUCKET_PARAMETER")
            arn = stack.format_arn(
                service="s3",
                region="",
                account="",
                resource=bucket,
                arn_format=ArnFormat.NO_RESOURCE_NAME,
            )
            resolved.extend((arn, f"{arn}/*"))
        elif resource == "dynamodb-table":
            table = _parameter_value(scope, environment, "DYNAMODB_TABLE_PARAMETER")
            arn = stack.format_arn(
                service="dynamodb", resource="table", resource_name=table
            )
            resolved.extend((arn, f"{arn}/index/*"))
        elif resource == "opensearch-domain":
            resolved.append(
                stack.format_arn(
                    service="es", resource="domain", resource_name=f"k9-{stage}-os/*"
                )
            )
        elif resource == "*" or resource.startswith("arn:"):
            resolved.append(resource)
        else:
            raise ValueError(f"Unknown IAM resource alias or ARN: {resource!r}")
    return resolved


def add_permissions(
    scope: Construct,
    function: lambda_.DockerImageFunction,
    stage: StageName,
    environment: Environment,
    grants: Sequence[Grant],
) -> None:
    for grant in grants:
        function.add_to_role_policy(
            iam.PolicyStatement(
                actions=grant.actions,
                resources=resolve_resources(scope, stage, environment, grant.resources),
                effect=iam.Effect.ALLOW if grant.effect == "allow" else iam.Effect.DENY,
            )
        )
