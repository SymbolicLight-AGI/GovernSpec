"""Thin stdio MCP server for GovernSpec."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from governspec_core import (
    SUPPORTED_TARGETS,
    compile_target,
    inspect_document,
    load_document,
    load_spec,
    resolve_document_imports,
    resolve_imports,
    test_output,
    validate_document,
    validate_spec,
)
from governspec_core.common.errors import (
    GovernSpecError,
    GovernSpecTestError,
    GovernSpecValidationError,
)
from governspec_core.common.utils import dump_json, read_text
from governspec_core.validator import ValidationReport

WORKSPACE_ROOT = Path.cwd().resolve()

_CANONICAL_TOOLS = [
    {
        "name": "governspec.validate",
        "description": "Validate a GovernSpec file.",
        "inputSchema": {
            "type": "object",
            "required": ["path"],
            "properties": {"path": {"type": "string"}},
        },
    },
    {
        "name": "governspec.inspect",
        "description": "Inspect the normalized IIR for a GovernSpec file.",
        "inputSchema": {
            "type": "object",
            "required": ["path"],
            "properties": {"path": {"type": "string"}},
        },
    },
    {
        "name": "governspec.compile",
        "description": "Compile a GovernSpec file into a target artifact.",
        "inputSchema": {
            "type": "object",
            "required": ["path", "target"],
            "properties": {
                "path": {"type": "string"},
                "target": {"type": "string"},
            },
        },
    },
    {
        "name": "governspec.test",
        "description": "Run acceptance tests for a GovernSpec file and an output artifact.",
        "inputSchema": {
            "type": "object",
            "required": ["path", "output_path"],
            "properties": {
                "path": {"type": "string"},
                "output_path": {"type": "string"},
            },
        },
    },
]
_TOOL_ALIASES = {
    "governspec_validate": "governspec.validate",
    "governspec_inspect": "governspec.inspect",
    "governspec_compile": "governspec.compile",
    "governspec_test": "governspec.test",
}
TOOLS = [
    *_CANONICAL_TOOLS,
    *[
        {
            **tool,
            "name": alias,
            "description": f"{tool['description']} Alias for {canonical}.",
        }
        for alias, canonical in _TOOL_ALIASES.items()
        for tool in _CANONICAL_TOOLS
        if tool["name"] == canonical
    ],
]


def main() -> None:
    while True:
        message = _read_message()
        if message is None:
            break
        response = handle_message(message)
        if response is not None:
            _write_message(response)


def handle_message(message: dict[str, Any]) -> dict[str, Any] | None:
    method = message.get("method")
    request_id = message.get("id")
    params = message.get("params", {})

    if method == "initialize":
        return _ok(
            request_id,
            {
                "protocolVersion": "2025-06-18",
                "serverInfo": {"name": "governspec-mcp", "version": "0.1.0"},
                "capabilities": {
                    "tools": {"listChanged": False},
                    "resources": {"subscribe": False},
                },
            },
        )
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return _ok(request_id, {"tools": TOOLS})
    if method == "tools/call":
        try:
            return _ok(request_id, {"content": [_tool_result(params)]})
        except Exception as exc:
            return _tool_error(request_id, exc)
    if method == "resources/list":
        return _ok(request_id, {"resources": _list_resources()})
    if method == "resources/read":
        try:
            return _ok(request_id, {"contents": [_read_resource(params.get("uri", ""))]})
        except Exception as exc:
            return _tool_error(request_id, exc)
    return _error(request_id, f"Unsupported method: {method}")


def _tool_result(params: dict[str, Any]) -> dict[str, Any]:
    name = _TOOL_ALIASES.get(params.get("name", ""), params.get("name", ""))
    arguments = params.get("arguments", {})
    path = (
        _resolve_workspace_path(arguments.get("path", ""), label="GovernSpec path")
        if arguments.get("path")
        else None
    )

    if name == "governspec.validate" and path is not None:
        document = resolve_document_imports(load_document(path))
        return {"type": "text", "text": dump_json(validate_document(document).to_dict())}
    if name == "governspec.inspect" and path is not None:
        document = _load_validated_document(path)
        return {"type": "text", "text": dump_json(inspect_document(document))}
    if name == "governspec.compile" and path is not None:
        spec = _load_validated_spec(path)
        artifact = compile_target(spec, str(arguments.get("target", "")))
        return {"type": "text", "text": dump_json(artifact.to_dict())}
    if name == "governspec.test" and path is not None:
        spec = _load_validated_spec(path)
        output_path = (
            _resolve_workspace_path(arguments.get("output_path", ""), label="Output path")
            if arguments.get("output_path")
            else None
        )
        if output_path is None or not output_path.exists():
            raise GovernSpecTestError(
                f"Output file not found: {output_path}",
                suggestion="Provide a readable output file path for governspec.test.",
            )
        if not output_path.is_file():
            raise GovernSpecTestError(
                f"Output path is not a file: {output_path}",
                suggestion="Provide a file path, not a directory, for governspec.test.",
            )
        output_text = read_text(output_path)
        report = test_output(spec, output_text)
        return {"type": "text", "text": dump_json(report.to_dict())}
    return {"type": "text", "text": dump_json({"ok": False, "error": "Unsupported tool call"})}


def _list_resources() -> list[dict[str, str]]:
    return [
        {
            "uri": "govern://spec/{path}",
            "name": "GovernSpec source",
            "mimeType": "application/yaml",
        },
        {
            "uri": "govern://iir/{path}",
            "name": "Normalized IIR",
            "mimeType": "application/json",
        },
        {
            "uri": "govern://compiled/{target}/{path}",
            "name": "Compiled GovernSpec artifact",
            "mimeType": "application/json",
        },
    ]


def _read_resource(uri: str) -> dict[str, str]:
    if uri.startswith("govern://spec/"):
        path = _resolve_workspace_path(
            uri.removeprefix("govern://spec/"),
            label="GovernSpec resource path",
        )
        load_document(path)
        return {"uri": uri, "mimeType": "application/yaml", "text": read_text(path)}
    if uri.startswith("govern://iir/"):
        path = _resolve_workspace_path(
            uri.removeprefix("govern://iir/"),
            label="IIR resource path",
        )
        document = _load_validated_document(path)
        return {
            "uri": uri,
            "mimeType": "application/json",
            "text": dump_json(inspect_document(document)),
        }
    if uri.startswith("govern://compiled/"):
        target, path = _parse_compiled_uri(uri)
        artifact = compile_target(_load_validated_spec(path), target)
        if artifact.kind == "bundle":
            return {
                "uri": uri,
                "mimeType": "application/json",
                "text": dump_json(
                    {
                        "kind": "bundle",
                        "target": target,
                        "files": artifact.files,
                    }
                ),
            }
        return {
            "uri": uri,
            "mimeType": "application/json" if _is_json_target(target) else "text/markdown",
            "text": artifact.content or "",
        }
    return {"uri": uri, "mimeType": "text/plain", "text": "Unknown resource"}


def _parse_compiled_uri(uri: str) -> tuple[str, Path]:
    resource = uri.removeprefix("govern://compiled/")
    if "/" not in resource:
        raise GovernSpecError(
            f"Invalid compiled resource URI: {uri}",
            suggestion=(
                "Use govern://compiled/<target>/<path>, for example "
                "govern://compiled/agents-md/<path>."
            ),
        )
    target, raw_path = resource.split("/", 1)
    normalized_target = target.strip().lower()
    if normalized_target not in SUPPORTED_TARGETS:
        raise GovernSpecError(
            f"Unsupported compiled resource target: {target}",
            suggestion=f"Use one of: {', '.join(sorted(SUPPORTED_TARGETS))}.",
            details={"target": target, "supported_targets": sorted(SUPPORTED_TARGETS)},
        )
    return normalized_target, _resolve_workspace_path(
        raw_path,
        label="Compiled resource path",
    )


def _resolve_workspace_path(raw_path: str | Path, *, label: str) -> Path:
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = WORKSPACE_ROOT / candidate
    resolved = candidate.resolve()
    try:
        resolved.relative_to(WORKSPACE_ROOT)
    except ValueError as exc:
        raise GovernSpecError(
            f"{label} must stay within the current working directory: {WORKSPACE_ROOT}",
            suggestion=(
                "Pass a path inside the current working directory used to start "
                "governspec-mcp."
            ),
            details={
                "path": str(resolved),
                "workspace_root": str(WORKSPACE_ROOT),
            },
        ) from exc
    return resolved


def _is_json_target(target: str) -> bool:
    return target in {"gemini-structured", "mcp-plan", "openai-json", "openai-structured"}


def _load_validated_document(path: Path) -> Any:
    document = resolve_document_imports(load_document(path))
    report = validate_document(document)
    _ensure_validation_report_ok(
        report,
        path,
        suggestion=(
            "Run governspec.validate first and fix the reported errors before "
            "inspecting this document."
        ),
    )
    return document


def _load_validated_spec(path: Path) -> Any:
    spec = resolve_imports(load_spec(path))
    report = validate_spec(spec)
    _ensure_validation_report_ok(
        report,
        path,
        suggestion=(
            "Run governspec.validate first and fix the reported errors before using "
            "this tool."
        ),
    )
    return spec


def _ensure_validation_report_ok(
    report: ValidationReport,
    path: Path,
    *,
    suggestion: str,
) -> None:
    if report.ok:
        return

    errors = report.errors or ["Unknown validation error."]
    raise GovernSpecValidationError(
        f"GovernSpec validation failed for {path}: {'; '.join(errors)}",
        suggestion=suggestion,
        details={
            "path": str(path),
            "errors": report.errors,
            "warnings": report.warnings,
        },
    )


def _read_message() -> dict[str, Any] | None:
    headers: dict[str, str] = {}
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return None
        decoded = line.decode("utf-8").strip()
        if not decoded:
            break
        key, value = decoded.split(":", 1)
        headers[key.lower()] = value.strip()
    length = int(headers.get("content-length", "0"))
    if length <= 0:
        return None
    body = sys.stdin.buffer.read(length)
    return json.loads(body.decode("utf-8"))


def _write_message(message: dict[str, Any]) -> None:
    body = json.dumps(message, ensure_ascii=False).encode("utf-8")
    sys.stdout.buffer.write(f"Content-Length: {len(body)}\r\n\r\n".encode("ascii"))
    sys.stdout.buffer.write(body)
    sys.stdout.buffer.flush()


def _ok(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id: Any, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": -32601, "message": message},
    }


def _tool_error(request_id: Any, exc: Exception) -> dict[str, Any]:
    if isinstance(exc, GovernSpecError):
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32000,
                "message": exc.message,
                "data": {"suggestion": exc.suggestion, "details": exc.details},
            },
        }
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": -32000, "message": str(exc)},
    }


if __name__ == "__main__":
    main()
