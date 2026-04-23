"""Packaged examples for IntentSpec."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from importlib.abc import Traversable
from pathlib import Path

from intentspec_core.common.utils import write_text


@dataclass(frozen=True, slots=True)
class ExampleFile:
    name: str
    filename: str


def list_examples() -> list[ExampleFile]:
    resource_dir = resources.files("intentspec_core.resources.examples")
    examples: list[ExampleFile] = []
    for relative_name, file in _walk_examples(resource_dir):
        if file.is_file() and file.name.endswith((".intent.yaml", ".output.md", ".output.json")):
            examples.append(ExampleFile(name=relative_name, filename=relative_name))
    return sorted(examples, key=lambda item: item.name)


def copy_example(name: str, destination: str | Path) -> Path:
    resource_name = name
    resource_file = resources.files("intentspec_core.resources.examples").joinpath(resource_name)
    if not resource_file.is_file():
        available = ", ".join(example.name for example in list_examples())
        raise FileNotFoundError(
            f"Unknown example '{name}'. Available examples: {available}"
        )
    destination_path = Path(destination)
    write_text(destination_path, resource_file.read_text(encoding="utf-8"))
    return destination_path


def _walk_examples(root: Traversable) -> list[tuple[str, Traversable]]:
    files: list[tuple[str, Traversable]] = []
    stack: list[tuple[str, Traversable]] = [("", root)]
    while stack:
        prefix, current = stack.pop()
        for child in current.iterdir():
            relative_name = f"{prefix}/{child.name}" if prefix else child.name
            if child.is_dir():
                stack.append((relative_name, child))
            else:
                files.append((relative_name, child))
    return files
