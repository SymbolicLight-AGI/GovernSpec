"""Environment diagnostics for GovernSpec v0.1."""

from __future__ import annotations

import sys
from dataclasses import asdict, dataclass, field
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from governspec_core.schemas import generate_json_schema

MIN_SUPPORTED_PYTHON = (3, 11)


@dataclass(slots=True)
class DoctorCheck:
    name: str
    status: str
    message: str


@dataclass(slots=True)
class DoctorReport:
    ok: bool
    python_version: str
    package_version: str
    checks: list[DoctorCheck] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_text(self) -> str:
        lines = [
            f"Doctor status: {'ok' if self.ok else 'failed'}",
            f"Python version: {self.python_version}",
            f"GovernSpec version: {self.package_version}",
            "Checks:",
        ]
        lines.extend(f"- [{check.status}] {check.name}: {check.message}" for check in self.checks)
        lines.append("Errors:" if self.errors else "Errors: none")
        if self.errors:
            lines.extend(f"- {item}" for item in self.errors)
        lines.append("Warnings:" if self.warnings else "Warnings: none")
        if self.warnings:
            lines.extend(f"- {item}" for item in self.warnings)
        return "\n".join(lines)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def run_doctor(cwd: Path) -> DoctorReport:
    checks: list[DoctorCheck] = []
    warnings: list[str] = []
    errors: list[str] = []

    python_version = ".".join(str(part) for part in sys.version_info[:3])
    if tuple(sys.version_info[:2]) < MIN_SUPPORTED_PYTHON:
        message = (
            f"Detected Python {python_version}, but GovernSpec requires "
            f"Python >= {MIN_SUPPORTED_PYTHON[0]}.{MIN_SUPPORTED_PYTHON[1]}."
        )
        checks.append(DoctorCheck("python_version", "error", message))
        errors.append(message)
    else:
        checks.append(DoctorCheck("python_version", "ok", f"Detected Python {python_version}."))

    package_version = _detect_package_version()
    checks.append(DoctorCheck("package_version", "ok", f"Detected GovernSpec {package_version}."))

    govern_file = cwd / "govern.yaml"
    if govern_file.exists():
        checks.append(DoctorCheck("govern_file", "ok", f"Found {govern_file.name} in {cwd}."))
    else:
        message = f"No govern.yaml found in {cwd}."
        checks.append(DoctorCheck("govern_file", "warning", message))
        warnings.append(message)

    try:
        schema = generate_json_schema()
        required_fields = schema.get("$defs", {}) or schema.get("properties", {})
        if required_fields:
            checks.append(
                DoctorCheck(
                    "schema_generation",
                    "ok",
                    "JSON Schema generated successfully.",
                )
            )
        else:
            message = "Generated JSON Schema is missing expected definitions."
            checks.append(DoctorCheck("schema_generation", "error", message))
            errors.append(message)
    except Exception as exc:  # pragma: no cover - defensive
        message = f"Failed to generate JSON Schema: {exc}"
        checks.append(DoctorCheck("schema_generation", "error", message))
        errors.append(message)

    return DoctorReport(
        ok=not errors,
        python_version=python_version,
        package_version=package_version,
        checks=checks,
        warnings=warnings,
        errors=errors,
    )


def _detect_package_version() -> str:
    try:
        return version("governspec")
    except PackageNotFoundError:
        return "0.1.0"
