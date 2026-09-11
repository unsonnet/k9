from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal

from aws_cdk import Duration, Stack
from aws_cdk import aws_apigatewayv2 as apigwv2
from aws_cdk import aws_apigatewayv2_authorizers as authorizers
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_lambda_event_sources as sources
from aws_cdk import aws_ssm as ssm
from aws_cdk.aws_apigatewayv2_integrations import HttpLambdaIntegration
from constructs import Construct
from pydantic import BaseModel, Field

from .config import ServiceConfig, StageName, WorkerConfig


def pascal_case(s: str) -> str:
    return "".join(
        part.capitalize() for part in s.replace("-", "_").replace(".", "_").split("_")
    )


class Grant(BaseModel):
    actions: list[str]
    resources: list[str] = Field(default_factory=lambda: ["*"])
    effect: Literal["allow", "deny"] = "allow"


class Route(BaseModel):
    rule: str
    method: apigwv2.HttpMethod
    auth_required: bool = False


class Event(BaseModel):
    event: Literal["INSERT", "MODIFY", "REMOVE"]
    type: str


class Manifest(BaseModel):
    grants: list[Grant] = Field(default_factory=list)
    routes: list[Route] = Field(default_factory=list)
    events: list[Event] = Field(default_factory=list)


def manifest(root: Path, kind: Literal["services", "workers"], name: str) -> Manifest:
    return Manifest.model_validate_json(
        (root / "cdk.out" / kind / f"{name}.json").read_text()
    )


def grant_resources(
    scope: Construct, stage: StageName, config: ServiceConfig, resources: list[str]
) -> list[str]:
    stack = Stack.of(scope)
    resolved: list[str] = []
    for resource in resources:
        match resource:
            case "cognito-user-pool" if parameter := config.environment.get(
                "COGNITO_USER_POOL_ID_PARAMETER"
            ):
                user_pool = ssm.StringParameter.value_for_string_parameter(
                    scope, parameter
                )
                resolved.append(
                    f"arn:aws:cognito-idp:{stack.region}:{stack.account}:userpool/{user_pool}"
                )
            case "s3-bucket" if parameter := config.environment.get(
                "S3_BUCKET_PARAMETER"
            ):
                bucket = ssm.StringParameter.value_for_string_parameter(
                    scope, parameter
                )
                resolved.extend((f"arn:aws:s3:::{bucket}", f"arn:aws:s3:::{bucket}/*"))
            case "dynamodb-table" if parameter := config.environment.get(
                "DYNAMODB_TABLE_PARAMETER"
            ):
                table = ssm.StringParameter.value_for_string_parameter(scope, parameter)
                resolved.extend(
                    (
                        f"arn:aws:dynamodb:{stack.region}:{stack.account}:table/{table}",
                        f"arn:aws:dynamodb:{stack.region}:{stack.account}:table/{table}/index/*",
                    )
                )
            case "opensearch-domain":
                resolved.append(
                    f"arn:aws:es:{stack.region}:{stack.account}:domain/k9-{stage}-os/*"
                )
            case "*":
                resolved.append(resource)
    return resolved


def create_function(
    scope: Construct,
    name: str,
    config: ServiceConfig,
    manifest: Manifest,
    *,
    stage: StageName,
    architecture: lambda_.Architecture,
    root: Path,
    kind: str,
) -> lambda_.DockerImageFunction:
    function = lambda_.DockerImageFunction(
        scope,
        "Function",
        function_name=f"k9-api-{stage}-{name.replace('.', '-')}",
        code=lambda_.DockerImageCode.from_image_asset(
            directory=str(root),
            file=config.dockerfile,
            cmd=[f"{name.replace('-', '_')}.handler.lambda_handler"],
        ),
        timeout=Duration.seconds(config.timeout),
        memory_size=config.memory,
        architecture=architecture,
        environment=config.environment,
    )
    for index, parameter in enumerate(
        (
            value
            for key, value in config.environment.items()
            if key.endswith("_PARAMETER")
        ),
        1,
    ):
        ssm.StringParameter.from_string_parameter_name(
            scope, f"{kind}Parameter{index}", parameter
        ).grant_read(function)
    for grant in manifest.grants:
        if resources := grant_resources(scope, stage, config, grant.resources):
            function.add_to_role_policy(
                iam.PolicyStatement(
                    actions=grant.actions,
                    resources=resources,
                    effect=iam.Effect.ALLOW
                    if grant.effect == "allow"
                    else iam.Effect.DENY,
                )
            )
    return function


def event_filters(events: list[Event]) -> list[Mapping[str, Any]]:
    grouped: dict[tuple[str, str], set[str]] = defaultdict(set)
    for event in events:
        image = "NewImage" if event.event in {"INSERT", "MODIFY"} else "OldImage"
        grouped[event.event, image].add(event.type)
    return [
        lambda_.FilterCriteria.filter(
            {
                "eventName": lambda_.FilterRule.is_equal(event),
                "dynamodb": {image: {"type": {"S": sorted(types)}}},
            }
        )
        for (event, image), types in grouped.items()
    ]


class ServiceRegistration(Construct):
    def __init__(
        self,
        scope: Construct,
        name: str,
        config: ServiceConfig,
        *,
        stage: StageName,
        architecture: lambda_.Architecture,
        root: Path,
        http: apigwv2.HttpApi,
        authorizer: authorizers.HttpJwtAuthorizer | None = None,
    ) -> None:
        super().__init__(scope, f"{pascal_case(name)}Service")
        definition = manifest(root, "services", name)
        self.function = create_function(
            self,
            name,
            config,
            definition,
            stage=stage,
            architecture=architecture,
            root=root,
            kind="Service",
        )
        integration = HttpLambdaIntegration("Integration", self.function)  # type: ignore
        for route in definition.routes:
            http.add_routes(
                path=route.rule.replace("<", "{").replace(">", "}"),
                methods=[route.method],
                integration=integration,
                authorizer=authorizer if route.auth_required else None,
            )


class WorkerRegistration(Construct):
    def __init__(
        self,
        scope: Construct,
        name: str,
        config: WorkerConfig,
        *,
        stage: StageName,
        architecture: lambda_.Architecture,
        root: Path,
    ) -> None:
        super().__init__(scope, f"{pascal_case(name)}Worker")
        definition = manifest(root, "workers", name)
        self.function = create_function(
            self,
            name,
            config,
            definition,
            stage=stage,
            architecture=architecture,
            root=root,
            kind="Worker",
        )
        table = dynamodb.Table.from_table_attributes(
            self,
            "SourceTable",
            table_name=config.table_name,
            table_stream_arn=ssm.StringParameter.value_for_string_parameter(
                self, config.stream_arn_parameter
            ),
        )
        table.grant_stream_read(self.function)
        self.function.add_event_source(
            sources.DynamoEventSource(
                table,
                starting_position=lambda_.StartingPosition.LATEST,
                batch_size=config.batch_size,
                retry_attempts=config.retry_attempts,
                report_batch_item_failures=config.report_batch_item_failures,
                bisect_batch_on_error=config.bisect_batch_on_error,
                filters=event_filters(definition.events),
                max_record_age=Duration.seconds(config.max_record_age_seconds)
                if config.max_record_age_seconds
                else None,
                max_batching_window=Duration.seconds(config.max_batching_window_seconds)
                if config.max_batching_window_seconds
                else None,
                parallelization_factor=config.parallelization_factor,
            )
        )
        if parameter := config.opensearch_collection_arn_parameter:
            collection = ssm.StringParameter.value_for_string_parameter(self, parameter)
            self.function.add_to_role_policy(
                iam.PolicyStatement(
                    actions=["aoss:APIAccessAll"], resources=[collection]
                )
            )
