from __future__ import annotations

from pathlib import Path

from aws_cdk import CfnOutput, Stack
from aws_cdk import aws_apigatewayv2 as apigwv2
from aws_cdk import aws_lambda as lambda_
from constructs import Construct

from .config import LambdaArchitecture, ServiceConfig, StageConfig, load_local_env_file
from .service import ServiceRegistration


def pascal_case(value: str) -> str:
    return "".join(part.capitalize() for part in value.replace("_", "-").split("-"))


def to_cdk_architecture(value: LambdaArchitecture) -> lambda_.Architecture:
    if value == LambdaArchitecture.ARM64:
        return lambda_.Architecture.ARM_64
    return lambda_.Architecture.X86_64


class K9ApiStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        config: StageConfig,
    ) -> None:
        super().__init__(
            scope,
            construct_id,
            env={"account": config.account, "region": config.region},
            description=f"K9 API infrastructure for {config.stage}",
        )

        repo_root = Path(__file__).resolve().parents[3]
        architecture = to_cdk_architecture(config.lambda_architecture)

        http_api = apigwv2.HttpApi(
            self,
            "HttpApi",
            api_name=f"k9-api-{config.stage}",
            create_default_stage=True,
        )

        for service_name, service_config in config.services.items():
            environment, readable_parameter_names = self._service_runtime_config(
                repo_root=repo_root,
                stage=config.stage,
                service_name=service_name,
                service_config=service_config,
                stage_config=config,
            )

            registration = ServiceRegistration(
                self,
                f"{pascal_case(service_name)}Service",
                repo_root=repo_root,
                http_api=http_api,
                service_name=service_name,
                stage=config.stage,
                config=service_config,
                architecture=architecture,
                environment=environment,
                readable_parameter_names=readable_parameter_names,
            )

            CfnOutput(
                self,
                f"{pascal_case(service_name)}FunctionName",
                value=registration.function.function_name,
            )

        CfnOutput(self, "ApiUrl", value=http_api.api_endpoint)

    def _service_runtime_config(
        self,
        *,
        repo_root: Path,
        stage: str,
        service_name: str,
        service_config: ServiceConfig,
        stage_config: StageConfig,
    ) -> tuple[dict[str, str], list[str]]:
        environment = dict(service_config.environment)
        readable_parameter_names = list(service_config.readable_parameter_names)

        if not service_config.uses_cognito:
            return environment, readable_parameter_names

        if stage == "dev":
            environment.update(
                load_local_env_file(repo_root, service_config.local_env_file)
            )
            return environment, readable_parameter_names

        identity = stage_config.shared.identity
        if identity is None:
            raise ValueError(
                f"Service {service_name!r} requires shared.identity in stage {stage!r}"
            )

        environment.update(identity.parameter_env)
        readable_parameter_names.extend(identity.parameter_env.values())
        return environment, readable_parameter_names
