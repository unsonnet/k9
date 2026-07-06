from enum import StrEnum
from typing import Literal

from aws_cdk import aws_lambda as lambda_
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Architecture(StrEnum):
    ARM64 = "arm64"
    X86_64 = "x86_64"

    @property
    def cdk(self) -> lambda_.Architecture:
        return {
            self.ARM64: lambda_.Architecture.ARM_64,
            self.X86_64: lambda_.Architecture.X86_64,
        }[self]


class FunctionConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    dockerfile: str
    timeout: int = 20
    memory: int = 512
    shared: list[str] = Field(default_factory=list)
    environment: dict[str, str] = Field(default_factory=dict)


class ServiceConfig(FunctionConfig):
    pass


class WorkerConfig(FunctionConfig):
    table_name: str = Field(alias="tableName")
    stream_arn_parameter: str = Field(alias="streamArnParameter")

    batch_size: int = Field(default=50, alias="batchSize")
    retry_attempts: int = Field(default=10, alias="retryAttempts")
    report_batch_item_failures: bool = Field(
        default=True,
        alias="reportBatchItemFailures",
    )
    bisect_batch_on_error: bool = Field(
        default=True,
        alias="bisectBatchOnError",
    )
    max_record_age_seconds: int | None = Field(
        default=None,
        alias="maxRecordAgeSeconds",
    )
    max_batching_window_seconds: int | None = Field(
        default=None,
        alias="maxBatchingWindowSeconds",
    )
    parallelization_factor: int | None = Field(
        default=None,
        alias="parallelizationFactor",
    )
    opensearch_collection_arn_parameter: str | None = Field(
        default=None,
        alias="opensearchCollectionArnParameter",
    )


type StageName = Literal["dev", "stage", "prod"]


class StageConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    stage: StageName
    account: str
    region: str
    architecture: Architecture = Architecture.ARM64
    shared: dict[str, dict[str, str]] = Field(default_factory=dict)
    services: dict[str, ServiceConfig] = Field(default_factory=dict)
    workers: dict[str, WorkerConfig] = Field(default_factory=dict)

    @model_validator(mode="after")
    def expand_environments(self) -> "StageConfig":
        global_env = {
            "APP_STAGE": self.stage,
            "APP_AWS_REGION": self.region,
        }
        missing: list[str] = []

        for name, config in {**self.services, **self.workers}.items():
            shared_env: dict[str, str] = {}

            for group in config.shared:
                values = self.shared.get(group)
                if values is None:
                    missing.append(f"{name}:{group}")
                    continue
                shared_env.update(values)

            config.environment = shared_env | config.environment | global_env

        if missing:
            raise ValueError(
                f"Undefined shared environment groups: {', '.join(missing)}"
            )

        return self
