"""Shared parsing helpers for IntentSpec importers."""

from __future__ import annotations

import re
from typing import Any

SECTION_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)
LIST_ITEM_RE = re.compile(r"^-\s+(.+)$", re.MULTILINE)
FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)

_PERMISSION_MAP: dict[str, tuple[str, str]] = {
    "web access": ("web", ""),
    "network access": ("network", ""),
    "filesystem read": ("filesystem", "read"),
    "filesystem write": ("filesystem", "write"),
    "tool send_email": ("tools", "send_email"),
    "tool read_calendar": ("tools", "read_calendar"),
    "tool read_gmail": ("tools", "read_gmail"),
    "tool create_file": ("tools", "create_file"),
    "tool delete_file": ("tools", "delete_file"),
    "tool purchase": ("tools", "purchase"),
}

_GATE_RE = re.compile(r"^(.+?)\s*->\s*(.+)$")

_OUTPUT_FORMAT_RE = re.compile(r"^Format:\s*(.+)$", re.IGNORECASE)
_OUTPUT_LANGUAGE_RE = re.compile(r"^Language:\s*(.+)$", re.IGNORECASE)
_OUTPUT_MAX_WORDS_RE = re.compile(r"^Max words:\s*(\d+)$", re.IGNORECASE)
_OUTPUT_SECTION_RE = re.compile(r"^Section:\s*(.+)$", re.IGNORECASE)
_OUTPUT_JSON_SCHEMA_RE = re.compile(r"^JSON Schema is required\.$", re.IGNORECASE)


def strip_frontmatter(text: str) -> str:
    match = FRONTMATTER_RE.match(text)
    if match:
        return text[match.end():]
    return text


def split_sections(body: str) -> dict[str, str]:
    """Split markdown body by ``## Heading`` into ``{heading: body_text}``."""
    headings = list(SECTION_RE.finditer(body))
    sections: dict[str, str] = {}
    for idx, heading_match in enumerate(headings):
        title = heading_match.group(1).strip()
        start = heading_match.end()
        end = headings[idx + 1].start() if idx + 1 < len(headings) else len(body)
        sections[title] = body[start:end]
    return sections


def extract_items(section_text: str) -> list[str]:
    """Return non-empty, non-"none" ``- item`` entries from *section_text*."""
    items = LIST_ITEM_RE.findall(section_text)
    return [item.strip() for item in items if item.strip() and item.strip() != "none"]


def parse_permissions(section_text: str) -> dict[str, Any]:
    """Parse an "Allowed and Forbidden Operations" section into a permissions dict."""
    permissions: dict[str, Any] = {
        "web": False,
        "filesystem": {"read": True, "write": False},
        "network": False,
        "tools": {
            "send_email": False,
            "read_calendar": False,
            "read_gmail": False,
            "create_file": False,
            "delete_file": False,
            "purchase": False,
        },
    }

    for line in extract_items(section_text):
        lowered = line.lower()
        for label, (group, subkey) in _PERMISSION_MAP.items():
            if label not in lowered:
                continue
            allowed = "allowed" in lowered
            if subkey:
                permissions[group][subkey] = allowed
            else:
                permissions[group] = allowed
            break

    return permissions


def parse_human_gates(section_text: str) -> list[dict[str, str]]:
    """Parse a "Human Confirmation Rules" section into a list of gate dicts."""
    gates: list[dict[str, str]] = []
    for item in extract_items(section_text):
        match = _GATE_RE.match(item)
        if match:
            gates.append({"when": match.group(1).strip(), "action": match.group(2).strip()})
    return gates


def parse_output(section_text: str) -> dict[str, Any]:
    """Parse an "Output Expectations" section into an output spec dict."""
    output: dict[str, Any] = {
        "format": "markdown",
        "language": "en",
        "max_words": 500,
        "sections": [],
    }

    for item in extract_items(section_text):
        fmt_match = _OUTPUT_FORMAT_RE.match(item)
        if fmt_match:
            output["format"] = fmt_match.group(1).strip()
            continue
        lang_match = _OUTPUT_LANGUAGE_RE.match(item)
        if lang_match:
            output["language"] = lang_match.group(1).strip()
            continue
        words_match = _OUTPUT_MAX_WORDS_RE.match(item)
        if words_match:
            output["max_words"] = int(words_match.group(1))
            continue
        section_match = _OUTPUT_SECTION_RE.match(item)
        if section_match:
            output["sections"].append(section_match.group(1).strip())
            continue
        if _OUTPUT_JSON_SCHEMA_RE.match(item):
            output["format"] = "json"
            continue

    if output["format"] == "json":
        return {
            "format": "json",
            "schema": {
                "type": "object",
                "properties": {},
            },
        }

    if not output["sections"]:
        output["sections"] = ["Summary"]

    return output


def build_verification_tests(verification_items: list[str]) -> list[dict[str, Any]]:
    """Convert verification step names into test case dicts."""
    tests: list[dict[str, Any]] = []
    for step in verification_items:
        tests.append({"name": step, "assert": [{"type": "required_sections"}]})
    if not tests:
        tests.append(
            {"name": "Must include all sections", "assert": [{"type": "required_sections"}]}
        )
    return tests


def default_permissions() -> dict[str, Any]:
    return {
        "web": False,
        "filesystem": {"read": True, "write": False},
        "network": False,
        "tools": {
            "send_email": False,
            "read_calendar": False,
            "read_gmail": False,
            "create_file": False,
            "delete_file": False,
            "purchase": False,
        },
    }


def build_draft_payload(
    *,
    goal: str,
    constraints: list[str],
    permissions: dict[str, Any],
    human_gates: list[dict[str, str]],
    output_spec: dict[str, Any],
    tests: list[dict[str, Any]],
    title: str = "",
    name: str = "imported_intent",
    audience: list[str] | None = None,
) -> dict[str, Any]:
    """Assemble a complete draft IntentSpec dict from parsed components."""
    return {
        "version": "0.1",
        "kind": "IntentSpec",
        "metadata": {
            "name": name,
            "title": (title or goal)[:80] if (title or goal) else "Imported intent",
            "description": title or goal,
            "owner": "imported",
        },
        "task": {
            "goal": goal,
            "audience": audience or ["Primary stakeholder"],
            "priority": "medium",
        },
        "context": {
            "domain": "General",
            "facts": [],
            "assumptions": [],
            "glossary": {},
        },
        "inputs": [],
        "permissions": permissions,
        "constraints": constraints or ["Do not fabricate facts."],
        "evidence": {
            "require_sources": False,
            "mark_uncertainty": True,
            "distinguish": ["fact", "inference"],
        },
        "output": output_spec,
        "quality": {"tone": ["clear"], "must_include": [], "must_avoid": []},
        "human_gates": human_gates,
        "tests": tests,
    }
