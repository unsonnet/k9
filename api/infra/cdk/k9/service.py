import ast
from pathlib import Path

from aws_cdk import Duration, Stack
from aws_cdk import aws_apigatewayv2 as apigwv2
from aws_cdk import aws_apigatewayv2_authorizers as apigwv2_authorizers
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_lambda_event_sources as event_sources
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_ssm as ssm
from aws_cdk.aws_apigatewayv2_integrations import HttpLambdaIntegration
from constructs import Construct

from .config import FunctionConfig, ServiceConfig, StageName, WorkerConfig

type ServiceRoute = tuple[apigwv2.HttpMethod, str, bool]


def pascal_case(name: str) -> str:
    return "".join(part.capitalize() for part in name.replace("-", "_").split("_"))


def normalize_route_path(route_prefix: str, rule: str) -> str:
    if rule == "/":
        return route_prefix
    return f"{route_prefix}{rule}".replace("<", "{").replace(">", "}")


def discover_service_routes(
    root: Path, name: str, route_prefix: str
) -> list[ServiceRoute]:
    handler_path = root / "services" / name / "src" / name / "handler.py"
    module = ast.parse(handler_path.read_text(), filename=str(handler_path))

    methods = {
        "get": apigwv2.HttpMethod.GET,
        "post": apigwv2.HttpMethod.POST,
        "put": apigwv2.HttpMethod.PUT,
        "patch": apigwv2.HttpMethod.PATCH,
        "delete": apigwv2.HttpMethod.DELETE,
    }

    routes: list[ServiceRoute] = []
    for node in module.body:
        if not isinstance(node, ast.FunctionDef):
            continue

        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            if not isinstance(decorator.func, ast.Attribute):
                continue

            method = methods.get(decorator.func.attr)
            if method is None or not decorator.args:
                continue

            rule_arg = decorator.args[0]
            if not isinstance(rule_arg, ast.Constant) or not isinstance(
                rule_arg.value, str
            ):
                continue

            auth_required = False
            if node.args.args:
                first_arg = node.args.args[0]
                auth_required = (
                    first_arg.arg == "caller"
                    and isinstance(first_arg.annotation, ast.Name)
                    and first_arg.annotation.id == "Caller"
                )

            routes.append(
                (
                    method,
                    normalize_route_path(route_prefix, rule_arg.value),
                    auth_required,
                )
            )

    return routes


def create_function(
    scope: Construct,
    *,
    stage: StageName,
    architecture: lambda_.Architecture,
    name: str,
    root: Path,
    config: FunctionConfig,
) -> lambda_.DockerImageFunction:
    fn = lambda_.DockerImageFunction(
        scope,
        "Function",
        function_name=f"k9-api-{stage}-{name}",
        code=lambda_.DockerImageCode.from_image_asset(
            directory=str(root),
            file=config.dockerfile,
        ),
        timeout=Duration.seconds(config.timeout),
        memory_size=config.memory,
        architecture=architecture,
        environment=config.environment,
    )

    for i, (key, parameter_name) in enumerate(config.environment.items(), start=1):
        if key.endswith("_PARAMETER"):
            ssm.StringParameter.from_string_parameter_name(
                scope,
                f"ReadableParameter{i}",
                parameter_name,
            ).grant_read(fn)

    if "COGNITO_USER_POOL_ID_PARAMETER" in config.environment:
        stack = Stack.of(scope)
        user_pool_id = ssm.StringParameter.value_for_string_parameter(
            scope,
            config.environment["COGNITO_USER_POOL_ID_PARAMETER"],
        )
        user_pool_arn = f"arn:aws:cognito-idp:{stack.region}:{stack.account}:userpool/{user_pool_id}"
        fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "cognito-idp:AdminCreateUser",
                    "cognito-idp:AdminDeleteUser",
                    "cognito-idp:AdminDisableUser",
                    "cognito-idp:AdminEnableUser",
                    "cognito-idp:AdminGetUser",
                    "cognito-idp:AdminInitiateAuth",
                    "cognito-idp:AdminRespondToAuthChallenge",
                    "cognito-idp:AdminSetUserMFAPreference",
                    "cognito-idp:AdminSetUserPassword",
                    "cognito-idp:AdminUpdateUserAttributes",
                    "cognito-idp:AdminUserGlobalSignOut",
                    "cognito-idp:AssociateSoftwareToken",
                    "cognito-idp:GetTokensFromRefreshToken",
                    "cognito-idp:ListUsers",
                    "cognito-idp:SetUserMFAPreference",
                    "cognito-idp:VerifySoftwareToken",
                ],
                resources=[user_pool_arn],
            )
        )

    if name in {"user", "company"} and "S3_BUCKET_PARAMETER" in config.environment:
        bucket_name = ssm.StringParameter.value_for_string_parameter(
            scope,
            config.environment["S3_BUCKET_PARAMETER"],
        )
        s3.Bucket.from_bucket_name(
            scope,
            "StorageBucket",
            bucket_name,
        ).grant_read_write(fn)

    if name == "company" and "DYNAMODB_TABLE_PARAMETER" in config.environment:
        table_base = ssm.StringParameter.value_for_string_parameter(
            scope,
            config.environment["DYNAMODB_TABLE_PARAMETER"],
        )
        dynamodb.Table.from_table_name(
            scope,
            "CompanyTable",
            f"{table_base}-companies",
        ).grant_read_write_data(fn)

    if (
        name in {"company", "company_index"}
        and "OPENSEARCH_ENDPOINT_PARAMETER" in config.environment
    ):
        stack = Stack.of(scope)
        domain_arn = f"arn:aws:es:{stack.region}:{stack.account}:domain/k9-{stage}-os/*"
        fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["es:ESHttp*"],
                resources=[domain_arn],
            )
        )

    if name == "company":
        fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["geo-places:Geocode"],
                resources=["*"],
            )
        )

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

        self.function = create_function(
            self,
            stage=stage,
            architecture=architecture,
            name=name,
            root=root,
            config=config,
        )

        integration = HttpLambdaIntegration("Integration", self.function)  # type: ignore[arg-type]

        for method, path, auth_required in discover_service_routes(
            root, name, config.route
        ):
            http.add_routes(
                path=path,
                methods=[method],
                integration=integration,
                authorizer=authorizer if auth_required else None,
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

        self.function = create_function(
            self,
            stage=stage,
            architecture=architecture,
            name=name,
            root=root,
            config=config,
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
