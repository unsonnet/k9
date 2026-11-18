import importlib
import pkgutil
from typing import Iterable

__all__ = [
    "load_apis",
]


def load_apis(package: str, path: Iterable[str]) -> None:
    for module in pkgutil.walk_packages(path, f"{package}."):
        if module.name.rpartition(".")[2] == "api":
            importlib.import_module(module.name)
