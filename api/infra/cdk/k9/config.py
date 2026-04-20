from enum import StrEnum

from aws_cdk import aws_lambda as lambda_
from pydantic import BaseModel, Field, model_validator


class Architecture(StrEnum):
    ARM64 = "arm64"
    X86_64 = "x86_64"

    def to_cdk(self) -> lambda_.Architecture:
        match self:
            case Architecture.ARM64:
                return lambda_.Architecture.ARM_64
            case Architecture.X86_64:
                return lambda_.Architecture.X86_64


class ServiceConfig(BaseModel):
    route: str = Field(alias="routePrefix")
    dockerfile: str
    timeout: int = 20
    memory: int = 512
    shared: list[str] = Field(default_factory=list)
    environment: dict[str, str] = Field(default_factory=dict)


class StageConfig(BaseModel):
    stage: str
    account: str
    region: str
    architecture: Architecture = Architecture.ARM64
    shared: dict[str, dict[str, str]] = Field(default_factory=dict)
    services: dict[str, ServiceConfig] = Field(..., min_length=1)

    @model_validator(mode="after")
    def expand_environments(self) -> "StageConfig":
        missing: list[str] = []

        glob = {"APP_STAGE": self.stage, "APP_AWS_REGION": self.region}
        for name, config in self.services.items():
            env: dict[str, str] = {}
            for group in config.shared:
                if group not in self.shared:
                    missing.append(f"{name}:{group}")
                    continue
                env.update(self.shared[group])
            config.environment = env | config.environment | glob

        if missing:
            raise ValueError(f"Undefined environment variables: {', '.join(missing)}")
        return self
