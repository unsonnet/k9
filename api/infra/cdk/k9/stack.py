from pathlib import Path

from aws_cdk import CfnOutput, Stack
from aws_cdk import aws_apigatewayv2 as apigwv2
from aws_cdk import aws_lambda as lambda_
from constructs import Construct

from .config import ServiceConfig, StageConfig
from .service import ServiceRegistration


def _register_services(
    stack: Stack,
    stage: str,
    arch: lambda_.Architecture,
    services: dict[str, ServiceConfig],
    *,
    root: Path,
    http: apigwv2.HttpApi,
) -> None:
    for name, config in services.items():
        service = ServiceRegistration(
            stack,
            stage,
            arch,
            name,
            config,
            root=root,
            http=http,
        )

        CfnOutput(
            stack,
            f"{name.capitalize()}FunctionName",
            value=service.function.function_name,
        )


def create_stack(
    scope: Construct,
    config: StageConfig,
) -> Stack:
    stack = Stack(
        scope,
        f"K9Api{config.stage.capitalize()}Stack",
        env={"account": config.account, "region": config.region},
        description=f"K9 API infrastructure for {config.stage}",
    )
    http = apigwv2.HttpApi(
        stack,
        "HttpApi",
        api_name=f"k9-api-{config.stage}",
        create_default_stage=True,
    )

    _register_services(
        stack,
        config.stage,
        config.architecture.to_cdk(),
        config.services,
        root=Path(__file__).resolve().parents[3],
        http=http,
    )

    CfnOutput(stack, "ApiUrl", value=http.api_endpoint)

    return stack
