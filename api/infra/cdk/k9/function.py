from pathlib import Path
from typing import cast

from aws_cdk import Duration, Tags
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_ssm as ssm
from constructs import Construct

from .config import Environment, ServiceConfig, StageName
from .image import Kind, image_code, package_name
from .manifest import Manifest
from .permissions import add_permissions


def create_function(
    scope: Construct,
    *,
    root: Path,
    kind: Kind,
    name: str,
    stage: StageName,
    architecture: lambda_.Architecture,
    config: ServiceConfig,
    environment: Environment,
    manifest: Manifest,
) -> lambda_.IFunction:
    physical_name = f"k9-api-{stage}-{package_name(kind, name)}"
    function = lambda_.DockerImageFunction(
        scope,
        "Function",
        function_name=physical_name,
        code=image_code(root, kind, name, architecture),
        architecture=architecture,
        timeout=Duration.seconds(config.timeout),
        memory_size=config.memory,
        environment=environment,
    )
    Tags.of(function).add("Name", physical_name)
    Tags.of(function).add("Component", kind[:-1])

    for index, parameter in enumerate(
        (value for key, value in environment.items() if key.endswith("_PARAMETER")), 1
    ):
        ssm.StringParameter.from_string_parameter_name(
            scope, f"Parameter{index}", parameter
        ).grant_read(function)

    add_permissions(scope, function, stage, environment, manifest.grants)
    return cast(lambda_.IFunction, function)
