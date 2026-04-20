from pathlib import Path
from typing import Iterable

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
        stage: str,
        arch: lambda_.Architecture,
        name: str,
        config: ServiceConfig,
        *,
        root: Path,
        http: apigwv2.HttpApi,
    ) -> None:
        super().__init__(scope, f"{name.capitalize()}Service")

        function = lambda_.DockerImageFunction(
            self,
            "Function",
            function_name=f"k9-api-{stage}-{name}",
            code=lambda_.DockerImageCode.from_image_asset(
                directory=str(root),
                file=config.dockerfile,
            ),
            timeout=Duration.seconds(config.timeout),
            memory_size=config.memory,
            architecture=arch,
            environment=config.environment,
        )

        integration = HttpLambdaIntegration("Integration", handler=function)  # type: ignore[arg-type]
        for path in (config.route, f"{config.route}/{{proxy+}}"):
            http.add_routes(
                path=path,
                methods=[apigwv2.HttpMethod.ANY],
                integration=integration,
            )

        self._grant_read_access(function, config.environment.keys())

        self.function = function

    def _grant_read_access(
        self,
        function: lambda_.DockerImageFunction,
        variables: Iterable[str],
    ) -> None:
        for index, name in enumerate(variables, start=1):
            if not name.endswith("_PARAMETER"):
                continue
            parameter = ssm.StringParameter.from_string_parameter_name(
                self,
                f"Readable{index}",
                name,
            )
            parameter.grant_read(function)
