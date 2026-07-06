import json
from pathlib import Path

from aws_cdk import Duration, Stack
from aws_cdk import aws_apigatewayv2 as apigwv2
from aws_cdk import aws_apigatewayv2_authorizers as apigwv2_authorizers
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_lambda_event_sources as event_sources
from aws_cdk import aws_ssm as ssm
from aws_cdk.aws_apigatewayv2_integrations import HttpLambdaIntegration
from constructs import Construct

from .config import FunctionConfig, ServiceConfig, StageName, WorkerConfig


def pascal_case(name: str) -> str:
    normalized = name.replace("-", "_").replace(".", "_")
    return "".join(part.capitalize() for part in normalized.split("_"))


def load_manifest(root: Path, kind: str, name: str) -> dict:
    path = root / "cdk.out" / kind / f"{name}.json"
    return json.loads(path.read_text())


def resolve_grant_resources(
    scope: Construct,
    *,
    stage: StageName,
    config: FunctionConfig,
    resources: list[str],
) -> list[str]:
    stack = Stack.of(scope)
    resolved: list[str] = []

    for resource in resources:
        match resource:
            case "cognito-user-pool":
                parameter = config.environment.get("COGNITO_USER_POOL_ID_PARAMETER")
                if not parameter:
                    continue
                user_pool_id = ssm.StringParameter.value_for_string_parameter(
                    scope, parameter
                )
                resolved.append(
                    f"arn:aws:cognito-idp:{stack.region}:{stack.account}:userpool/{user_pool_id}"
                )
            case "s3-bucket":
                parameter = config.environment.get("S3_BUCKET_PARAMETER")
                if not parameter:
                    continue
                bucket_name = ssm.StringParameter.value_for_string_parameter(
                    scope, parameter
                )
                resolved.extend(
                    [f"arn:aws:s3:::{bucket_name}", f"arn:aws:s3:::{bucket_name}/*"]
                )
            case "dynamodb-table":
                parameter = config.environment.get("DYNAMODB_TABLE_PARAMETER")
                if not parameter:
                    continue
                table_base = ssm.StringParameter.value_for_string_parameter(
                    scope, parameter
                )
                resolved.append(
                    f"arn:aws:dynamodb:{stack.region}:{stack.account}:table/{table_base}-*"
                )
            case "opensearch-domain":
                resolved.append(
                    f"arn:aws:es:{stack.region}:{stack.account}:domain/k9-{stage}-os/*"
                )
            case "*":
                resolved.append("*")
            case _:
                resolved.append(resource)

    return resolved


def apply_manifest_grants(
    scope: Construct,
    *,
    fn: lambda_.DockerImageFunction,
    stage: StageName,
    config: FunctionConfig,
    manifest: dict,
) -> None:
    for grant in manifest.get("grants", []):
        actions = grant.get("actions") or []
        resources = resolve_grant_resources(
            scope,
            stage=stage,
            config=config,
            resources=list(grant.get("resources") or ["*"]),
        )
        if actions and resources:
            fn.add_to_role_policy(
                iam.PolicyStatement(actions=actions, resources=resources)
            )


def apply_parameter_reads(
    scope: Construct,
    fn: lambda_.DockerImageFunction,
    *,
    prefix: str,
    config: FunctionConfig,
) -> None:
    index = 0
    for key, parameter_name in config.environment.items():
        if not key.endswith("_PARAMETER"):
            continue
        index += 1
        ssm.StringParameter.from_string_parameter_name(
            scope,
            f"{prefix}Parameter{index}",
            parameter_name,
        ).grant_read(fn)


def create_function(
    scope: Construct,
    *,
    kind: str,
    stage: StageName,
    architecture: lambda_.Architecture,
    name: str,
    root: Path,
    config: FunctionConfig,
    manifest: dict,
) -> lambda_.DockerImageFunction:
    module_name = name.replace("-", "_")
    function_suffix = name.replace(".", "-")
    fn = lambda_.DockerImageFunction(
        scope,
        "Function",
        function_name=f"k9-api-{stage}-{function_suffix}",
        code=lambda_.DockerImageCode.from_image_asset(
            directory=str(root),
            file=config.dockerfile,
            cmd=[f"{module_name}.handler.lambda_handler"],
        ),
        timeout=Duration.seconds(config.timeout),
        memory_size=config.memory,
        architecture=architecture,
        environment=config.environment,
    )

    apply_parameter_reads(scope, fn, prefix=pascal_case(kind), config=config)
    apply_manifest_grants(scope, fn=fn, stage=stage, config=config, manifest=manifest)
    return fn


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
        authorizer: apigwv2_authorizers.HttpJwtAuthorizer | None = None,
    ) -> None:
        super().__init__(scope, f"{pascal_case(name)}Service")

        manifest = load_manifest(root, "services", name)
        self.function = create_function(
            self,
            kind="service",
            stage=stage,
            architecture=architecture,
            name=name,
            root=root,
            config=config,
            manifest=manifest,
        )

        integration = HttpLambdaIntegration("Integration", self.function)  # type: ignore[arg-type]
        for route in manifest.get("routes", []):
            http.add_routes(
                path=route["rule"].replace("<", "{").replace(">", "}"),
                methods=[apigwv2.HttpMethod(route["method"])],
                integration=integration,
                authorizer=authorizer if route.get("auth_required") else None,
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
        self.function = create_function(
            self,
            kind="worker",
            stage=stage,
            architecture=architecture,
            name=name,
            root=root,
            config=config,
            manifest=manifest,
        )

        stream_arn = ssm.StringParameter.value_for_string_parameter(
            self,
            config.stream_arn_parameter,
        )

        table = dynamodb.Table.from_table_attributes(
            self,
            "SourceTable",
            table_name=config.table_name,
            table_stream_arn=stream_arn,
        )
        table.grant_stream_read(self.function)

        self.function.add_event_source(
            event_sources.DynamoEventSource(
                table,
                starting_position=lambda_.StartingPosition.LATEST,
                batch_size=config.batch_size,
                retry_attempts=config.retry_attempts,
                report_batch_item_failures=config.report_batch_item_failures,
                bisect_batch_on_error=config.bisect_batch_on_error,
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

        if config.opensearch_collection_arn_parameter:
            collection_arn = ssm.StringParameter.value_for_string_parameter(
                self,
                config.opensearch_collection_arn_parameter,
            )
            self.function.add_to_role_policy(
                iam.PolicyStatement(
                    actions=["aoss:APIAccessAll"],
                    resources=[collection_arn],
                )
            )
