import shutil
import subprocess
from pathlib import Path
from typing import Literal

from aws_cdk import aws_ecr_assets as ecr_assets
from aws_cdk import aws_lambda as lambda_

type Kind = Literal["services", "workers"]
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", "*.pyd")
DOCKERFILE = Path(__file__).resolve().parents[1] / "Dockerfile"


def package_name(kind: Kind, name: str) -> str:
    return f"{kind[:-1]}-{name.replace('_', '-')}"


def stage_context(root: Path, kind: Kind, name: str) -> Path:
    """Stage exported third-party dependencies and editable workspace sources."""
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
            member = (root / line[3:].strip()).resolve()
            if not member.is_relative_to(root) or not (member / "src").is_dir():
                raise ValueError(f"Invalid editable package source: {member}")
            members.add(member)
        else:
            requirements.append(line)

    if not members:
        raise ValueError(f"No editable workspace sources exported for {package}")
    if not DOCKERFILE.is_file():
        raise FileNotFoundError(DOCKERFILE)

    context = root / ".build" / "images" / package
    shutil.rmtree(context, ignore_errors=True)
    (context / "src").mkdir(parents=True)
    (context / "requirements.txt").write_text(
        "\n".join(requirements) + "\n", encoding="utf-8"
    )
    for member in sorted(members):
        shutil.copytree(
            member / "src", context / "src", dirs_exist_ok=True, ignore=IGNORE
        )
    shutil.copyfile(DOCKERFILE, context / "Dockerfile")
    return context


def image_code(
    root: Path, kind: Kind, name: str, architecture: lambda_.Architecture
) -> lambda_.DockerImageCode:
    platform = (
        ecr_assets.Platform.LINUX_ARM64
        if architecture == lambda_.Architecture.ARM_64
        else ecr_assets.Platform.LINUX_AMD64
    )
    return lambda_.DockerImageCode.from_image_asset(
        directory=str(stage_context(root, kind, name)),
        cmd=[f"{name}.lambda_handler"],
        platform=platform,
    )
