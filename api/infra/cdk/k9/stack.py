from pathlib import Path

from aws_cdk import CfnOutput, Environment, Stack, Tags
from aws_cdk import aws_apigatewayv2 as apigwv2
from aws_cdk import aws_apigatewayv2_authorizers as authorizers
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_ssm as ssm
from constructs import Construct

from .config import StageConfig
from .service import ServiceRegistration
from .worker import WorkerRegistration


def _authorizer(
    stack: Stack, config: StageConfig
) -> authorizers.HttpJwtAuthorizer | None:
    identity = config.shared.get("identity")
    if identity is None:
        return None
    try:
        pool_parameter = identity["COGNITO_USER_POOL_ID_PARAMETER"]
        client_parameter = identity["COGNITO_CLIENT_ID_PARAMETER"]
    except KeyError as exc:
        raise ValueError(f"Missing Cognito identity configuration: {exc}") from exc
    pool_id = ssm.StringParameter.value_for_string_parameter(stack, pool_parameter)
    client_id = ssm.StringParameter.value_for_string_parameter(stack, client_parameter)
    return authorizers.HttpJwtAuthorizer(
        "CognitoAuthorizer",
        jwt_issuer=f"https://cognito-idp.{config.region}.amazonaws.com/{pool_id}",
        jwt_audience=[client_id],
    )


def create_stack(scope: Construct, config: StageConfig) -> Stack:
    root = Path(__file__).resolve().parents[3]
    stack = Stack(
        scope,
        f"K9Api{config.stage.capitalize()}Stack",
        env=Environment(account=config.account, region=config.region),
        description=f"K9 API infrastructure for {config.stage}",
    )
    for key, value in (
        ("Application", "k9-api"),
        ("Environment", config.stage),
        ("ManagedBy", "aws-cdk"),
    ):
        Tags.of(stack).add(key, value)

    http = apigwv2.HttpApi(
        stack,
        "HttpApi",
        api_name=f"k9-api-{config.stage}",
        create_default_stage=True,
    )
    Tags.of(http).add("Name", f"k9-api-{config.stage}")
    auth = _authorizer(stack, config)

    for name, service_config in config.services.items():
        service = ServiceRegistration(
            stack,
            name,
            service_config,
            stage=config.stage,
            architecture=config.architecture.cdk,
            root=root,
            environment=config.environment_for(service_config),
            http=http,
            authorizer=auth,
        )
        CfnOutput(
            stack,
            f"{service.node.id}FunctionName",
            value=service.function.function_name,
        )

    source_buckets: dict[str, s3.IBucket] = {}
    for name, worker_config in config.workers.items():
        worker = WorkerRegistration(
            stack,
            name,
            worker_config,
            stage=config.stage,
            architecture=config.architecture.cdk,
            root=root,
            environment=config.environment_for(worker_config),
            source_buckets=source_buckets,
        )
        CfnOutput(
            stack, f"{worker.node.id}FunctionName", value=worker.function.function_name
        )

    CfnOutput(stack, "ApiUrl", value=http.api_endpoint)
    return stack
