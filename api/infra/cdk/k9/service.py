from pathlib import Path

from aws_cdk import aws_apigatewayv2 as apigwv2
from aws_cdk import aws_apigatewayv2_authorizers as authorizers
from aws_cdk import aws_lambda as lambda_
from aws_cdk.aws_apigatewayv2_integrations import HttpLambdaIntegration
from constructs import Construct

from .config import Environment, ServiceConfig, StageName
from .function import create_function
from .manifest import load_manifest


def _construct_id(prefix: str, name: str) -> str:
    return prefix + "".join(
        part.capitalize()
        for part in name.replace("-", "_").replace(".", "_").split("_")
    )


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
        environment: Environment,
        http: apigwv2.HttpApi,
        authorizer: authorizers.HttpJwtAuthorizer | None,
    ) -> None:
        super().__init__(scope, _construct_id("Service", name))
        manifest = load_manifest(root, "services", name)
        if manifest.events:
            raise ValueError(f"HTTP service {name!r} must not declare worker events")
        if any(route.auth_required for route in manifest.routes) and authorizer is None:
            raise ValueError(f"Service {name!r} requires an HTTP authorizer")

        self.function = create_function(
            self,
            root=root,
            kind="services",
            name=name,
            stage=stage,
            architecture=architecture,
            config=config,
            environment=environment,
            manifest=manifest,
        )
        integration = HttpLambdaIntegration("Integration", handler=self.function)
        for route in manifest.routes:
            http.add_routes(
                path=route.rule.replace("<", "{").replace(">", "}"),
                methods=[route.method],
                integration=integration,
                authorizer=authorizer if route.auth_required else None,
            )
