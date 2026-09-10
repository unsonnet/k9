from enum import StrEnum
from itertools import chain
from typing import Literal, Self

from aws_cdk import aws_lambda as lambda_
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Architecture(StrEnum):
    ARM64 = "arm64"
    X86_64 = "x86_64"

    @property
    def cdk(self) -> lambda_.Architecture:
        return (
            lambda_.Architecture.ARM_64
            if self is self.ARM64
            else lambda_.Architecture.X86_64
        )


def camel_case(s: str) -> str:
    head, *tail = s.split("_")
    return head + "".join(part.capitalize() for part in tail)


class ServiceConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=camel_case)

    dockerfile: str
    timeout: int = 20
    memory: int = 512
    shared: list[str] = Field(default_factory=list)
    environment: dict[str, str] = Field(default_factory=dict)


class WorkerConfig(ServiceConfig):
    table_name: str
    stream_arn_parameter: str
    batch_size: int = 50
    retry_attempts: int = 10
    report_batch_item_failures: bool = True
    bisect_batch_on_error: bool = True
    max_record_age_seconds: int | None = None
    max_batching_window_seconds: int | None = None
    parallelization_factor: int | None = None
    opensearch_collection_arn_parameter: str | None = None


type StageName = Literal["dev", "stage", "prod"]
type Environment = dict[str, str]


class StageConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    stage: StageName
    account: str
    region: str
    architecture: Architecture = Architecture.ARM64
    shared: dict[str, Environment] = Field(default_factory=dict)
    services: dict[str, ServiceConfig] = Field(default_factory=dict)
    workers: dict[str, WorkerConfig] = Field(default_factory=dict)

    @model_validator(mode="after")
    def expand_environments(self) -> Self:
        app = {"APP_STAGE": self.stage, "APP_AWS_REGION": self.region}
        for config in chain(self.services.values(), self.workers.values()):
            shared = {k: v for g in config.shared for k, v in self.shared[g].items()}
            config.environment = shared | config.environment | app
        return self
