from enum import StrEnum
from typing import Annotated, Literal, Self

from aws_cdk import aws_lambda as lambda_
from pydantic import BaseModel, ConfigDict, Field, model_validator

type StageName = Literal["dev", "stage", "prod"]
type Environment = dict[str, str]


class Architecture(StrEnum):
    ARM64 = "arm64"
    X86_64 = "x86_64"

    @property
    def cdk(self) -> lambda_.Architecture:
        return {
            Architecture.ARM64: lambda_.Architecture.ARM_64,
            Architecture.X86_64: lambda_.Architecture.X86_64,
        }[self]


def _camel_case(value: str) -> str:
    head, *tail = value.split("_")
    return head + "".join(part.capitalize() for part in tail)


class _Config(BaseModel):
    model_config = ConfigDict(
        extra="forbid", populate_by_name=True, alias_generator=_camel_case
    )


class ServiceConfig(_Config):
    timeout: int = Field(20, ge=1, le=900)
    memory: int = Field(512, ge=128, le=10240)
    shared: list[str] = Field(default_factory=list)
    environment: Environment = Field(default_factory=dict)


class DynamoDBWorkerConfig(ServiceConfig):
    source: Literal["dynamodb"]
    table_name: str
    stream_arn_parameter: str
    batch_size: int = Field(50, ge=1, le=1000)
    retry_attempts: int = Field(10, ge=0, le=10000)
    report_batch_item_failures: bool = True
    bisect_batch_on_error: bool = True
    max_record_age_seconds: int | None = Field(None, ge=60, le=604800)
    max_batching_window_seconds: int | None = Field(None, ge=0, le=300)
    parallelization_factor: int | None = Field(None, ge=1, le=10)
    opensearch_collection_arn_parameter: str | None = None


class S3WorkerConfig(ServiceConfig):
    source: Literal["s3"]
    bucket_name: str
    opensearch_collection_arn_parameter: str | None = None


type WorkerConfig = Annotated[
    DynamoDBWorkerConfig | S3WorkerConfig, Field(discriminator="source")
]


def _interpolate(value: object, variables: dict[str, str]) -> object:
    """Expand only known placeholders, rejecting accidental/unresolved fields."""
    if isinstance(value, str):
        for key, replacement in variables.items():
            value = value.replace("{" + key + "}", replacement)
        return value
    if isinstance(value, list):
        return [_interpolate(item, variables) for item in value]
    if isinstance(value, dict):
        return {key: _interpolate(item, variables) for key, item in value.items()}
    return value


class StageConfig(_Config):
    stage: StageName
    account: str = Field(pattern=r"^\d{12}$")
    region: str = Field(min_length=1)
    architecture: Architecture = Architecture.ARM64
    shared: dict[str, Environment] = Field(default_factory=dict)
    services: dict[str, ServiceConfig] = Field(default_factory=dict)
    workers: dict[str, WorkerConfig] = Field(default_factory=dict)

    @classmethod
    def from_context(cls, context: dict[str, object]) -> Self:
        stage = context.get("stage")
        if not isinstance(stage, str) or stage not in ("dev", "stage", "prod"):
            raise ValueError("CDK context must specify stage: dev, stage, or prod")
        account, region = context.get("account"), context.get("region")
        if not isinstance(account, str) or not isinstance(region, str):
            raise ValueError("CDK context requires string account and region")
        keys = ("architecture", "shared", "services", "workers")
        selected = {key: context[key] for key in keys if key in context}
        data = {"stage": stage, "account": account, "region": region, **selected}
        variables = {"stage": stage, "account": account, "region": region}
        return cls.model_validate(_interpolate(data, variables))

    @model_validator(mode="after")
    def validate_shared_groups(self) -> Self:
        for name, config in (*self.services.items(), *self.workers.items()):
            missing = set(config.shared) - self.shared.keys()
            if missing:
                raise ValueError(f"{name}: unknown shared groups: {sorted(missing)}")
        return self

    def environment_for(self, config: ServiceConfig) -> Environment:
        """Resolve shared values without mutating the original configuration."""
        result: Environment = {}
        for group in config.shared:
            result.update(self.shared[group])
        result.update(config.environment)
        result.update(APP_STAGE=self.stage, APP_AWS_REGION=self.region)
        return result
