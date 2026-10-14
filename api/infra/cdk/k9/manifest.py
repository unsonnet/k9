from pathlib import Path
from typing import Annotated, Literal

from aws_cdk import aws_apigatewayv2 as apigwv2
from pydantic import BaseModel, ConfigDict, Field

from .image import Kind


class _ManifestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Grant(_ManifestModel):
    actions: list[str] = Field(min_length=1)
    resources: list[str] = Field(default_factory=lambda: ["*"], min_length=1)
    effect: Literal["allow", "deny"] = "allow"


class Route(_ManifestModel):
    rule: str
    method: apigwv2.HttpMethod
    auth_required: bool = False
    operation_id: str | None = None
    summary: str | None = None
    tags: list[str] = Field(default_factory=list)


class DynamoDBEvent(_ManifestModel):
    source: Literal["dynamodb"]
    event: Literal["INSERT", "MODIFY", "REMOVE"]
    rule: str


class S3Event(_ManifestModel):
    source: Literal["s3"]
    event: Literal["OBJECT_CREATED", "OBJECT_REMOVED"]
    rule: str


type Event = Annotated[DynamoDBEvent | S3Event, Field(discriminator="source")]


class Manifest(_ManifestModel):
    services: str | None = None
    workers: str | None = None
    grants: list[Grant] = Field(default_factory=list)
    routes: list[Route] = Field(default_factory=list)
    events: list[Event] = Field(default_factory=list)


def load_manifest(root: Path, kind: Kind, name: str) -> Manifest:
    path = root / "infra" / "cdk" / "cdk.out" / "manifests" / kind / f"{name}.json"
    if not path.is_file():
        raise FileNotFoundError(f"Missing generated manifest: {path}")
    manifest = Manifest.model_validate_json(path.read_text(encoding="utf-8"))
    other_kind = "workers" if kind == "services" else "services"
    if getattr(manifest, kind) != name or getattr(manifest, other_kind) is not None:
        raise ValueError(f"Manifest identity does not match {kind}.{name}: {path}")
    return manifest
