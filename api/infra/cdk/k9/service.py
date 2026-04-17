from __future__ import annotations

from pathlib import Path

from aws_cdk import Duration
from aws_cdk import aws_apigatewayv2 as apigwv2
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_ssm as ssm
from aws_cdk.aws_apigatewayv2_integrations import HttpLambdaIntegration
from constructs import Construct

from .config import ServiceConfig


class ServiceRegistration(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        repo_root: Path,
        http_api: apigwv2.HttpApi,
        service_name: str,
        stage: str,
        config: ServiceConfig,
        architecture: lambda_.Architecture,
        environment: dict[str, str],
        readable_parameter_names: list[str],
    ) -> None:
        super().__init__(scope, construct_id)

        function = lambda_.DockerImageFunction(
            self,
            "Function",
            function_name=f"k9-api-{stage}-{service_name}",
            code=lambda_.DockerImageCode.from_image_asset(
                directory=str(repo_root),
                file=config.dockerfile,
            ),
            timeout=Duration.seconds(config.timeout),
            memory_size=config.memory,
            architecture=architecture,
            environment=environment,
        )

        integration = HttpLambdaIntegration("Integration", handler=function)  # type: ignore[arg-type]

        for path in (config.route_prefix, f"{config.route_prefix}/{{proxy+}}"):
            http_api.add_routes(
                path=path,
                methods=[apigwv2.HttpMethod.ANY],
                integration=integration,
            )

        for index, parameter_name in enumerate(
            dict.fromkeys(readable_parameter_names), start=1
        ):
            parameter = ssm.StringParameter.from_string_parameter_name(
                self,
                f"ReadableParam{index}",
                parameter_name,
            )
            parameter.grant_read(function)

        self.function = function
