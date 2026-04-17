from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from aws_cdk import App
from pydantic import BaseModel, Field, model_validator


class LambdaArchitecture(StrEnum):
    ARM64 = "arm64"
    X86_64 = "x86_64"


class IdentityConfig(BaseModel):
    parameter_env: dict[str, str] = Field(default_factory=dict, alias="parameterEnv")


class SharedConfig(BaseModel):
    identity: IdentityConfig | None = None


class ServiceConfig(BaseModel):
    route_prefix: str = Field(alias="routePrefix")
    dockerfile: str
    timeout: int = 20
    memory: int = 512
    uses_cognito: bool = Field(default=False, alias="usesCognito")
    local_env_file: str | None = Field(default=None, alias="localEnvFile")
    environment: dict[str, str] = Field(default_factory=dict)
    readable_parameter_names: list[str] = Field(
        default_factory=list,
        alias="readableParameterNames",
    )


class StageConfig(BaseModel):
    stage: str
    account: str
    region: str
    lambda_architecture: LambdaArchitecture = Field(
        default=LambdaArchitecture.ARM64,
        alias="lambdaArchitecture",
    )
    shared: SharedConfig = Field(default_factory=SharedConfig)
    services: dict[str, ServiceConfig]

    @model_validator(mode="after")
    def validate_services(self) -> "StageConfig":
        if not self.services:
            raise ValueError("At least one service must be configured")
        return self


def load_stage_config(app: App, stage: str) -> StageConfig:
    raw = app.node.try_get_context(stage)
    if not isinstance(raw, dict):
        raise ValueError(f"Missing or invalid context for stage {stage!r}")

    return StageConfig.model_validate(
        {
            **raw,
            "stage": stage,
        }
    )


def load_local_env_file(repo_root: Path, env_file: str | None) -> dict[str, str]:
    if not env_file:
        return {}

    path = repo_root / env_file
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values
