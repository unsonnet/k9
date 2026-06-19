from pathlib import Path

from aws_cdk import CfnOutput, Environment, Stack
from aws_cdk import aws_apigatewayv2 as apigwv2
from aws_cdk import aws_apigatewayv2_authorizers as apigwv2_authorizers
from aws_cdk import aws_ssm as ssm
from constructs import Construct

from .config import StageConfig
from .service import ServiceRegistration, WorkerRegistration, pascal_case


def create_stack(scope: Construct, config: StageConfig) -> Stack:
    root = Path(__file__).resolve().parents[3]

    stack = Stack(
        scope,
        f"K9Api{config.stage.capitalize()}Stack",
        env=Environment(account=config.account, region=config.region),
        description=f"K9 API infrastructure for {config.stage}",
    )

    http = apigwv2.HttpApi(
        stack,
        "HttpApi",
        api_name=f"k9-api-{config.stage}",
        create_default_stage=True,
    )

    identity = config.shared.get("identity")
    authorizer: apigwv2_authorizers.HttpJwtAuthorizer | None = None
    if identity is not None:
        user_pool_id = ssm.StringParameter.value_for_string_parameter(
            stack,
            identity["COGNITO_USER_POOL_ID_PARAMETER"],
        )
        client_id = ssm.StringParameter.value_for_string_parameter(
            stack,
            identity["COGNITO_CLIENT_ID_PARAMETER"],
        )
        authorizer = apigwv2_authorizers.HttpJwtAuthorizer(
            "CognitoAuthorizer",
            jwt_issuer=f"https://cognito-idp.{config.region}.amazonaws.com/{user_pool_id}",
            jwt_audience=[client_id],
        )

    for name, service_config in config.services.items():
        service = ServiceRegistration(
            stack,
            name,
            service_config,
            stage=config.stage,
            architecture=config.architecture.cdk,
            root=root,
            http=http,
            authorizer=authorizer,
        )
        CfnOutput(
            stack,
            f"{pascal_case(name)}ServiceFunctionName",
            value=service.function.function_name,
        )

    for name, worker_config in config.workers.items():
        worker = WorkerRegistration(
            stack,
            name,
            worker_config,
            stage=config.stage,
            architecture=config.architecture.cdk,
            root=root,
        )
        CfnOutput(
            stack,
            f"{pascal_case(name)}WorkerFunctionName",
            value=worker.function.function_name,
        )

    CfnOutput(stack, "ApiUrl", value=http.api_endpoint)
    return stack
