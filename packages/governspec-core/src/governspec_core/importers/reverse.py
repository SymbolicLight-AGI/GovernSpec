"""Unified entry point for reverse-importing artifacts into GovernSpec drafts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from governspec_core.common.errors import GovernSpecParseError
from governspec_core.common.utils import read_text
from governspec_core.importers.cursor_rules import import_cursor_rules
from governspec_core.importers.gemini_structured import import_gemini_structured
from governspec_core.importers.instruction_markdown import import_instruction_markdown
from governspec_core.importers.openai_structured import import_openai_structured

SUPPORTED_IMPORT_TYPES = {
    "agents-md",
    "claude-md",
    "cursor-rules",
    "gemini-structured",
    "openai-structured",
}

_EXTENSION_HINTS: dict[str, str] = {
    ".mdc": "cursor-rules",
}

_MARKDOWN_IMPORT_TYPES = {"agents-md", "claude-md"}

_FILENAME_HINTS: dict[str, str] = {
    "agents.md": "agents-md",
    "claude.md": "claude-md",
}


def import_from_artifact(
    source_path: Path,
    source_type: str | None = None,
) -> dict[str, Any]:
    """Read *source_path* and return a draft GovernSpec payload dict.

    When *source_type* is ``None`` the function tries to infer it from the
    file extension and content.
    """
    text = _read_source(source_path)
    resolved_type = source_type or _infer_type(source_path, text)

    if resolved_type == "openai-structured":
        return import_openai_structured(_parse_json(text, source_path))
    if resolved_type == "gemini-structured":
        return import_gemini_structured(_parse_json(text, source_path))
    if resolved_type == "cursor-rules":
        return import_cursor_rules(text)
    if resolved_type in _MARKDOWN_IMPORT_TYPES:
        return import_instruction_markdown(text)

    raise GovernSpecParseError(
        f"Unsupported import source type: {resolved_type}",
        suggestion=f"Use one of: {', '.join(sorted(SUPPORTED_IMPORT_TYPES))}.",
        details={
            "source_type": resolved_type,
            "supported_types": sorted(SUPPORTED_IMPORT_TYPES),
        },
    )


def import_from_string(
    text: str,
    source_type: str,
) -> dict[str, Any]:
    """Import from an in-memory string (useful for SDK / MCP callers)."""
    if source_type == "openai-structured":
        return import_openai_structured(_parse_json_text(text))
    if source_type == "gemini-structured":
        return import_gemini_structured(_parse_json_text(text))
    if source_type == "cursor-rules":
        return import_cursor_rules(text)
    if source_type in _MARKDOWN_IMPORT_TYPES:
        return import_instruction_markdown(text)

    raise GovernSpecParseError(
        f"Unsupported import source type: {source_type}",
        suggestion=f"Use one of: {', '.join(sorted(SUPPORTED_IMPORT_TYPES))}.",
        details={
            "source_type": source_type,
            "supported_types": sorted(SUPPORTED_IMPORT_TYPES),
        },
    )


def _read_source(path: Path) -> str:
    try:
        return read_text(path)
    except OSError as exc:
        raise GovernSpecParseError(
            f"Cannot read import source: {path}",
            suggestion="Verify the file exists and is readable.",
            details={"path": str(path)},
        ) from exc


def _parse_json(text: str, source_path: Path) -> dict[str, Any]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise GovernSpecParseError(
            f"Import source is not valid JSON: {source_path}",
            suggestion="Provide a valid JSON file.",
            details={"path": str(source_path)},
        ) from exc
    if not isinstance(data, dict):
        raise GovernSpecParseError(
            "Import source JSON must be an object at the top level.",
            suggestion="Provide a JSON object, not an array or scalar.",
        )
    return data


def _parse_json_text(text: str) -> dict[str, Any]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise GovernSpecParseError(
            "Import source is not valid JSON.",
            suggestion="Provide a valid JSON string.",
        ) from exc
    if not isinstance(data, dict):
        raise GovernSpecParseError(
            "Import source JSON must be an object at the top level.",
            suggestion="Provide a JSON object, not an array or scalar.",
        )
    return data


def _infer_type(path: Path, text: str) -> str:
    suffix = path.suffix.lower()
    if suffix in _EXTENSION_HINTS:
        return _EXTENSION_HINTS[suffix]

    filename_lower = path.name.lower()
    if filename_lower in _FILENAME_HINTS:
        return _FILENAME_HINTS[filename_lower]

    if suffix == ".json":
        try:
            data = json.loads(text)
        except (json.JSONDecodeError, ValueError):
            raise GovernSpecParseError(
                f"Cannot infer import type for: {path}",
                suggestion="Pass --type explicitly.",
            )
        if isinstance(data, dict):
            if "json_schema" in data:
                return "openai-structured"
            if "generationConfig" in data:
                return "gemini-structured"

    if suffix == ".md" and text.strip():
        return "agents-md"

    raise GovernSpecParseError(
        f"Cannot infer import type from file: {path}",
        suggestion=(
            f"Pass --type explicitly. Supported types: "
            f"{', '.join(sorted(SUPPORTED_IMPORT_TYPES))}."
        ),
        details={"path": str(path)},
    )
