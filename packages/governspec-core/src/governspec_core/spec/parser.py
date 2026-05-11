"""YAML parser for GovernSpec v0.1."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from governspec_core.common.errors import (
    GovernSpecFileError,
    GovernSpecParseError,
    GovernSpecValidationError,
)
from governspec_core.spec.models import GovernDocument, GovernDocumentAdapter, GovernSpec


def load_document(path: str | Path) -> GovernDocument:
    document_path = Path(path)
    if not document_path.exists():
        raise GovernSpecFileError(
            f"GovernSpec file not found: {document_path}",
            suggestion="Check the file path and try again.",
            details={"path": str(document_path)},
        )
    if not document_path.is_file():
        raise GovernSpecFileError(
            f"GovernSpec path is not a file: {document_path}",
            suggestion="Provide a path to a .yaml file instead of a directory.",
            details={"path": str(document_path)},
        )

    try:
        raw_text = document_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise GovernSpecFileError(
            f"Unable to read GovernSpec file: {document_path}",
            suggestion="Verify the file exists and that you have read permission.",
            details={"path": str(document_path)},
        ) from exc

    try:
        payload = yaml.safe_load(raw_text)
    except yaml.YAMLError as exc:
        raise GovernSpecParseError(
            _build_parse_error_message(document_path, exc),
            suggestion="Check indentation, quoting, and list formatting near the reported line.",
            details=_build_parse_error_details(document_path, exc),
        ) from exc

    if not isinstance(payload, Mapping):
        raise GovernSpecValidationError(
            f"GovernSpec validation failed for {document_path}: root: expected a YAML mapping",
            suggestion="Start the file with top-level keys like version, kind, metadata, and task.",
            details={"path": str(document_path)},
        )

    try:
        document = GovernDocumentAdapter.validate_python(payload)
    except ValidationError as exc:
        error_details = exc.errors(include_url=False)
        raise GovernSpecValidationError(
            _build_validation_error_message(document_path, error_details),
            suggestion=_suggest_validation_fix(error_details),
            details={"path": str(document_path), "errors": error_details},
        ) from exc

    document._source_path = document_path.resolve()
    return document


def load_spec(path: str | Path) -> GovernSpec:
    document = load_document(path)
    if not isinstance(document, GovernSpec):
        source_path = getattr(document, "_source_path", Path(path))
        raise GovernSpecValidationError(
            f"Expected a GovernSpec document, but found kind={document.kind}.",
            suggestion=(
                "Use a GovernSpec file for validate/compile/test or import this "
                "pack from another spec."
            ),
            details={"path": str(source_path), "kind": document.kind},
        )
    return document


def _build_parse_error_message(document_path: Path, exc: yaml.YAMLError) -> str:
    details = _build_parse_error_details(document_path, exc)
    line = details.get("line")
    column = details.get("column")
    problem = details.get("problem")
    message = f"Invalid YAML in {document_path}"
    if line is not None and column is not None:
        message += f" at line {line}, column {column}"
    elif line is not None:
        message += f" at line {line}"
    if problem:
        message += f": {problem}"
    return message


def _build_parse_error_details(document_path: Path, exc: yaml.YAMLError) -> dict[str, Any]:
    details: dict[str, Any] = {"path": str(document_path)}
    mark = getattr(exc, "problem_mark", None)
    if mark is not None:
        details["line"] = mark.line + 1
        details["column"] = mark.column + 1
    problem = getattr(exc, "problem", None)
    if problem:
        details["problem"] = problem
    return details


def _build_validation_error_message(
    document_path: Path, error_details: Sequence[Mapping[str, Any]]
) -> str:
    if not error_details:
        return f"GovernSpec validation failed for {document_path}."
    first_error = error_details[0]
    location = ".".join(str(item) for item in first_error.get("loc", ())) or "<root>"
    return (
        f"GovernSpec validation failed for {document_path}: "
        f"{location}: {first_error.get('msg', 'Unknown validation error')}"
    )


def _suggest_validation_fix(error_details: Sequence[Mapping[str, Any]]) -> str:
    if not error_details:
        return "Review the schema examples and align the file with the v0.1 schema."
    first_error = error_details[0]
    location = ".".join(str(item) for item in first_error.get("loc", ())) or "<root>"
    error_type = str(first_error.get("type", ""))
    if location == "task.goal":
        return "Add a non-empty task.goal field under task."
    if error_type == "missing":
        return f"Add the missing required field '{location}' and run validate again."
    if error_type in {"literal_error", "union_tag_invalid"}:
        return f"Use an allowed value for '{location}' and check the v0.1 schema."
    if error_type == "extra_forbidden":
        return f"Remove the unsupported field '{location}' to match the v0.1 schema."
    return "Review the reported field and align it with the v0.1 schema before retrying."
