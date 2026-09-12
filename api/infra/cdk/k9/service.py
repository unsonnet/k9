from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path
from typing import Annotated, Any, Literal, cast

from aws_cdk import Duration, Stack
from aws_cdk import aws_apigatewayv2 as apigwv2
from aws_cdk import aws_apigatewayv2_authorizers as authorizers
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_lambda_event_sources as sources
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_notifications as s3_notifications
from aws_cdk import aws_ssm as ssm
from aws_cdk.aws_apigatewayv2_integrations import HttpLambdaIntegration
from constructs import Construct
from pydantic import BaseModel, Field

from .config import (
    DynamoDBWorkerConfig,
    S3WorkerConfig,
    ServiceConfig,
    StageName,
    WorkerConfig,
)


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


class DynamoDBEvent(BaseModel):
    source: Literal["dynamodb"]
    event: Literal["INSERT", "MODIFY", "REMOVE"]
    rule: str


class S3Event(BaseModel):
    source: Literal["s3"]
    event: Literal["Object_Created", "Object_Removed"]
    rule: str


type Event = Annotated[
    DynamoDBEvent | S3Event,
    Field(discriminator="source"),
]


class Manifest(BaseModel):
    grants: list[Grant] = Field(default_factory=list)
    routes: list[Route] = Field(default_factory=list)
    events: list[Event] = Field(default_factory=list)


def load_manifest(
    root: Path,
    kind: Literal["services", "workers"],
    name: str,
) -> Manifest:
    return Manifest.model_validate_json(
        (root / "cdk.out" / kind / f"{name}.json").read_text()
    )


def grant_resources(
    scope: Construct,
    stage: StageName,
    config: ServiceConfig,
    resources: list[str],
) -> list[str]:
    stack = Stack.of(scope)
    resolved: list[str] = []
    for resource in resources:
        match resource:
            case "cognito-user-pool":
                user_pool = ssm.StringParameter.value_for_string_parameter(
                    scope,
                    config.environment["COGNITO_USER_POOL_ID_PARAMETER"],
                )
                resolved.append(
                    f"arn:aws:cognito-idp:{stack.region}:{stack.account}:"
                    f"userpool/{user_pool}"
                )

            case "s3-bucket":
                bucket = ssm.StringParameter.value_for_string_parameter(
                    scope,
                    config.environment["S3_BUCKET_PARAMETER"],
                )
                resolved += [
                    f"arn:aws:s3:::{bucket}",
                    f"arn:aws:s3:::{bucket}/*",
                ]

            case "dynamodb-table":
                table = ssm.StringParameter.value_for_string_parameter(
                    scope,
                    config.environment["DYNAMODB_TABLE_PARAMETER"],
                )
                arn = f"arn:aws:dynamodb:{stack.region}:{stack.account}:table/{table}"
                resolved += [arn, f"{arn}/index/*"]

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

    parameters = (p for k, p in config.environment.items() if k.endswith("_PARAMETER"))
    for index, parameter in enumerate(parameters, 1):
        ssm.StringParameter.from_string_parameter_name(
            scope,
            f"Parameter{index}",
            parameter,
        ).grant_read(function)

    for grant in manifest.grants:
        function.add_to_role_policy(
            iam.PolicyStatement(
                actions=grant.actions,
                resources=grant_resources(
                    scope,
                    stage,
                    config,
                    grant.resources,
                ),
                effect=iam.Effect.ALLOW if grant.effect == "allow" else iam.Effect.DENY,
            )
        )

    return function


def dynamodb_filters(events: list[DynamoDBEvent]) -> list[Mapping[str, Any]]:
    grouped: dict[tuple[str, str], set[str]] = defaultdict(set)
    for event in events:
        image = "NewImage" if event.event in {"INSERT", "MODIFY"} else "OldImage"
        grouped[event.event, image].add(event.rule)
    return [
        lambda_.FilterCriteria.filter(
            {
                "eventName": lambda_.FilterRule.is_equal(event),
                "dynamodb": {image: {"type": {"S": sorted(rules)}}},
            }
        )
        for (event, image), rules in grouped.items()
    ]


def s3_filter(rule: str) -> s3.NotificationKeyFilter:
    prefix, _, suffix = rule.partition("*")
    return s3.NotificationKeyFilter(prefix=prefix or None, suffix=suffix or None)


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

        manifest = load_manifest(root, "services", name)
        self.function = create_function(
            self,
            name,
            config,
            manifest,
            stage=stage,
            architecture=architecture,
            root=root,
        )

        integration = HttpLambdaIntegration(
            "Integration",
            handler=cast(lambda_.IFunction, self.function),
        )

        for route in manifest.routes:
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

        manifest = load_manifest(root, "workers", name)
        if any(event.source != config.source for event in manifest.events):
            raise ValueError(
                f"{name!r} contains events that do not match its "
                f"{config.source!r} worker source"
            )

        self.function = create_function(
            self,
            name,
            config,
            manifest,
            stage=stage,
            architecture=architecture,
            root=root,
        )

        match config:
            case DynamoDBWorkerConfig():
                self._bind_dynamodb(config, cast(list[DynamoDBEvent], manifest.events))
            case S3WorkerConfig():
                self._bind_s3(config, cast(list[S3Event], manifest.events))

        if parameter := config.opensearch_collection_arn_parameter:
            collection = ssm.StringParameter.value_for_string_parameter(
                self,
                parameter,
            )
            self.function.add_to_role_policy(
                iam.PolicyStatement(
                    actions=["aoss:APIAccessAll"],
                    resources=[collection],
                )
            )

    def _bind_dynamodb(
        self,
        config: DynamoDBWorkerConfig,
        events: list[DynamoDBEvent],
    ) -> None:
        table = dynamodb.Table.from_table_attributes(
            self,
            "SourceTable",
            table_name=config.table_name,
            table_stream_arn=ssm.StringParameter.value_for_string_parameter(
                self,
                config.stream_arn_parameter,
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
                filters=dynamodb_filters(events),
                max_record_age=(
                    Duration.seconds(config.max_record_age_seconds)
                    if config.max_record_age_seconds is not None
                    else None
                ),
                max_batching_window=(
                    Duration.seconds(config.max_batching_window_seconds)
                    if config.max_batching_window_seconds is not None
                    else None
                ),
                parallelization_factor=config.parallelization_factor,
            )
        )

    def _bind_s3(
        self,
        config: S3WorkerConfig,
        events: list[S3Event],
    ) -> None:
        bucket = s3.Bucket.from_bucket_name(self, "SourceBucket", config.bucket_name)
        destination = s3_notifications.LambdaDestination(
            cast(lambda_.IFunction, self.function)
        )

        for event in events:
            bucket.add_event_notification(
                s3.EventType(event.event),
                destination,
                s3_filter(event.rule),
            )
