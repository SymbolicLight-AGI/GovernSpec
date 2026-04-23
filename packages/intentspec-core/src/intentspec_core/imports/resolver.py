"""IntentSpec import resolution."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from intentspec_core.common.errors import IntentSpecValidationError
from intentspec_core.common.utils import dedupe_preserve_order, deep_merge_dict, resolve_path
from intentspec_core.spec.models import IntentDocument, IntentPack, IntentSpec
from intentspec_core.spec.parser import load_document

_MERGEABLE_FIELDS = {"permissions", "constraints", "human_gates", "tests", "quality", "evidence"}


def resolve_imports(spec: IntentSpec) -> IntentSpec:
    resolved = resolve_document_imports(spec)
    if not isinstance(resolved, IntentSpec):
        raise IntentSpecValidationError("Resolved document is not an IntentSpec.")
    return resolved


def resolve_document_imports(document: IntentDocument) -> IntentDocument:
    resolved_payload, resolved_paths = _resolve_document(document, stack=[])
    resolved: IntentDocument
    if isinstance(document, IntentSpec):
        resolved = IntentSpec.model_validate(resolved_payload)
    else:
        resolved = IntentPack.model_validate(resolved_payload)
    resolved._source_path = document._source_path
    resolved._resolved_imports = resolved_paths
    return resolved


def _resolve_document(
    document: IntentDocument,
    *,
    stack: list[Path],
) -> tuple[dict[str, Any], list[Path]]:
    source_path = document._source_path
    if source_path is None:
        raise IntentSpecValidationError("Loaded document is missing source path metadata.")
    normalized_source = source_path.resolve()
    if normalized_source in stack:
        cycle = " -> ".join(str(item) for item in [*stack, normalized_source])
        raise IntentSpecValidationError(
            f"Import cycle detected: {cycle}",
            suggestion="Remove the circular import so packs resolve in a directed graph.",
            details={"cycle": [str(item) for item in [*stack, normalized_source]]},
        )

    merged_fragment: dict[str, Any] = {}
    resolved_paths: list[Path] = []
    next_stack = [*stack, normalized_source]

    for import_entry in document.imports:
        imported_path = resolve_path(source_path, import_entry).resolve()
        imported_document = load_document(imported_path)
        imported_payload, nested_paths = _resolve_document(imported_document, stack=next_stack)
        imported_fragment = _extract_mergeable_fragment(imported_payload)
        merged_fragment = _merge_fragments(merged_fragment, imported_fragment)
        resolved_paths.extend(nested_paths)
        if imported_path not in resolved_paths:
            resolved_paths.append(imported_path)

    local_payload = document.model_dump(by_alias=True, exclude_none=True)
    local_fragment = _extract_mergeable_fragment(local_payload)
    merged_fragment = _merge_fragments(merged_fragment, local_fragment)

    if isinstance(document, IntentPack):
        pack_payload = {
            "version": document.version,
            "kind": document.kind,
            "metadata": local_payload["metadata"],
            "imports": document.imports,
            **merged_fragment,
        }
        return pack_payload, resolved_paths

    resolved_payload = {**local_payload, **merged_fragment}
    return resolved_payload, resolved_paths


def _extract_mergeable_fragment(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in payload.items()
        if key in _MERGEABLE_FIELDS and value not in (None, [], {})
    }


def _merge_fragments(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in incoming.items():
        if key == "constraints":
            merged[key] = dedupe_preserve_order([*merged.get(key, []), *value])
        elif key == "human_gates":
            merged[key] = _merge_human_gates(merged.get(key, []), value)
        elif key == "tests":
            merged[key] = _merge_tests(merged.get(key, []), value)
        elif key == "permissions":
            merged[key] = _merge_permissions(merged.get(key), value)
        elif key in {"quality", "evidence"}:
            merged[key] = deep_merge_dict(merged.get(key, {}), value)
        else:
            merged[key] = value
    return merged


def _merge_human_gates(
    base_items: list[dict[str, Any]],
    incoming_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for item in [*base_items, *incoming_items]:
        key = (str(item.get("when", "")), str(item.get("action", "")))
        if key in seen:
            continue
        seen.add(key)
        merged.append(item)
    return merged


def _merge_tests(
    base_items: list[dict[str, Any]],
    incoming_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    ordered: list[str] = []
    items_by_name: dict[str, dict[str, Any]] = {}
    for item in [*base_items, *incoming_items]:
        name = str(item.get("name", ""))
        if not name:
            continue
        if name not in items_by_name:
            ordered.append(name)
            items_by_name[name] = item
            continue
        items_by_name[name] = _merge_test_case(items_by_name[name], item)
    return [items_by_name[name] for name in ordered if name]


def _merge_test_case(base_item: dict[str, Any], incoming_item: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base_item)
    merged["name"] = incoming_item.get("name", base_item.get("name", ""))
    merged["assert"] = dedupe_preserve_order(
        [
            *list(base_item.get("assert", [])),
            *list(incoming_item.get("assert", [])),
        ]
    )
    return merged


def _merge_permissions(
    base_value: dict[str, Any] | None,
    incoming_value: dict[str, Any],
) -> dict[str, Any]:
    if base_value is None:
        return incoming_value

    merged = dict(base_value)
    for key, value in incoming_value.items():
        current = merged.get(key)
        if isinstance(value, dict):
            merged[key] = _merge_permissions(current or {}, value)
        elif isinstance(value, bool):
            merged[key] = bool(current) and value if key in merged else value
        else:
            merged[key] = value
    return merged
