import shutil
import subprocess
from pathlib import Path
from typing import Literal

from aws_cdk import aws_ecr_assets as ecr_assets
from aws_cdk import aws_lambda as lambda_

DOCKERFILE = Path(__file__).resolve().parents[1] / "Dockerfile"
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", "*.pyd")

type Kind = Literal["services", "workers"]


def package_name(kind: Kind, name: str) -> str:
    prefix = "service" if kind == "services" else "worker"
    return f"{prefix}-{name.replace('_', '-')}"


def stage_context(root: Path, kind: Kind, name: str) -> Path:
    """Stage a package's locked dependency closure as a Docker context."""
    root = root.resolve()
    package = package_name(kind, name)
    export = subprocess.run(
        [
            "uv",
            "export",
            "--project",
            str(root),
            "--package",
            package,
            "--locked",
            "--no-dev",
            "--no-header",
            "--no-annotate",
            "--format",
            "requirements.txt",
        ],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout

    members: set[Path] = set()
    requirements: list[str] = []
    for line in export.splitlines():
        if line.startswith("-e "):
            members.add((root / line.removeprefix("-e ").strip()).resolve())
        else:
            requirements.append(line)

    context = root / ".build" / "images" / package
    shutil.rmtree(context, ignore_errors=True)
    (context / "src").mkdir(parents=True)
    (context / "requirements.txt").write_text("\n".join(requirements) + "\n")
    for member in sorted(members):
        shutil.copytree(
            member / "src",
            context / "src",
            dirs_exist_ok=True,
            ignore=IGNORE,
        )

    shutil.copyfile(DOCKERFILE, context / "Dockerfile")
    return context


def image_code(
    root: Path,
    kind: Kind,
    name: str,
    architecture: lambda_.Architecture,
) -> lambda_.DockerImageCode:
    return lambda_.DockerImageCode.from_image_asset(
        directory=str(stage_context(root, kind, name)),
        cmd=[f"{name}.lambda_handler"],
        platform=(
            ecr_assets.Platform.LINUX_ARM64
            if architecture == lambda_.Architecture.ARM_64
            else ecr_assets.Platform.LINUX_AMD64
        ),
    )
