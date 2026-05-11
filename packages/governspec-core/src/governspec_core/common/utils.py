"""Shared utility helpers."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

_CJK_PATTERN = re.compile(r"[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]")
_MARKDOWN_PREFIX_PATTERN = re.compile(
    r"(?m)^\s{0,3}(?:#{1,6}|\*|-|\+|>|\d+[.)])\s+"
)
_ALNUM_PATTERN = re.compile(r"[A-Za-z0-9]")
_SEGMENT_PATTERN = re.compile(r"\.([A-Za-z_][A-Za-z0-9_]*)|\[(\d+)\]")

def read_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def write_text(path: str | Path, content: str) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")


def resolve_path(base_path: Path | None, value: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute() or base_path is None:
        return candidate
    return base_path.parent / candidate


def estimate_word_count(text: str) -> float:
    normalized_text = _normalize_text_for_word_count(text)
    cjk_chars = _CJK_PATTERN.findall(normalized_text)
    non_cjk_text = _CJK_PATTERN.sub(" ", normalized_text)
    english_words = [
        token for token in non_cjk_text.split() if _ALNUM_PATTERN.search(token)
    ]
    return len(english_words) + (len(cjk_chars) / 2)


def format_count(value: float) -> str:
    if math.isclose(value, int(value)):
        return str(int(value))
    return f"{value:.1f}".rstrip("0").rstrip(".")


def dump_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def deep_merge_dict(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in incoming.items():
        current = merged.get(key)
        if isinstance(current, dict) and isinstance(value, dict):
            merged[key] = deep_merge_dict(current, value)
        elif isinstance(current, list) and isinstance(value, list):
            merged[key] = dedupe_preserve_order([*current, *value])
        else:
            merged[key] = value
    return merged


def dedupe_preserve_order(items: list[Any]) -> list[Any]:
    seen: set[str] = set()
    result: list[Any] = []
    for item in items:
        marker = json.dumps(item, ensure_ascii=False, sort_keys=True, default=str)
        if marker in seen:
            continue
        seen.add(marker)
        result.append(item)
    return result


def find_json_path(data: Any, path: str) -> tuple[bool, Any]:
    if path == "$":
        return True, data
    if not path.startswith("$"):
        return False, None
    current = data
    index = 1
    while index < len(path):
        match = _SEGMENT_PATTERN.match(path, index)
        if match is None:
            return False, None
        field_name, index_value = match.groups()
        if field_name is not None:
            if not isinstance(current, dict) or field_name not in current:
                return False, None
            current = current[field_name]
        else:
            if not isinstance(current, list):
                return False, None
            item_index = int(index_value)
            if item_index >= len(current):
                return False, None
            current = current[item_index]
        index = match.end()
    return True, current


def render_markdown_list(items: list[str]) -> str:
    if not items:
        return "- none"
    return "\n".join(f"- {item}" for item in items)


def heuristic_draft_payload(prompt: str) -> dict[str, Any]:
    """Generate a draft GovernSpec payload from a free-text prompt.

    Delegates to :func:`governspec_core.draft.heuristic_draft_payload`.
    """
    from governspec_core.draft import heuristic_draft_payload as _impl

    return _impl(prompt)


def _normalize_text_for_word_count(text: str) -> str:
    normalized = _MARKDOWN_PREFIX_PATTERN.sub("", text)
    return normalized.replace("`", " ")
