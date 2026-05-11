"""Import AGENTS.md / CLAUDE.md instruction documents into GovernSpec drafts.

Supports two parsing modes:

1. **GovernSpec-generated** documents — recognized by the fixed section
   structure emitted by ``compile_target(spec, "agents-md"|"claude-md")``.
   These are parsed precisely.

2. **Hand-written** documents — any markdown file with ``#``/``##`` headings.
   A heuristic layer extracts goal, constraints, permissions, and gates
   from free-form content.
"""

from __future__ import annotations

import re
from typing import Any

from governspec_core.common.errors import GovernSpecParseError
from governspec_core.importers._parsing import (
    build_draft_payload,
    build_verification_tests,
    default_permissions,
    extract_items,
    parse_human_gates,
    parse_output,
    parse_permissions,
    split_sections,
    strip_frontmatter,
)

_INTENTSPEC_GENERATED_SECTIONS = {
    "Project Goal",
    "Working Constraints",
    "Allowed and Forbidden Operations",
    "Human Confirmation Rules",
    "Output Expectations",
    "Verification Steps",
}

_H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)

_PERMISSION_DENY_PATTERNS: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(r"(?:do\s+)?not\s+(?:access|use)\s+(?:the\s+)?(?:web|internet)", re.I),
     "web", ""),
    (re.compile(r"(?:no|without|disable)\s+network", re.I),
     "network", ""),
    (re.compile(r"read[- ]?only", re.I),
     "filesystem", "write"),
    (re.compile(r"(?:do\s+)?not\s+(?:modify|edit|write|create|delete)\s+(?:any\s+)?files?", re.I),
     "filesystem", "write"),
    (re.compile(r"(?:do\s+)?not\s+send\s+(?:any\s+)?emails?", re.I),
     "tools", "send_email"),
    (re.compile(r"(?:do\s+)?not\s+(?:make\s+)?purchas", re.I),
     "tools", "purchase"),
    (re.compile(r"(?:do\s+)?not\s+delete", re.I),
     "tools", "delete_file"),
]

_PERMISSION_ALLOW_PATTERNS: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(r"(?:may|can|allowed?\s+to)\s+(?:access|use)\s+(?:the\s+)?(?:web|internet)", re.I),
     "web", ""),
    (re.compile(r"(?:may|can|allowed?\s+to)\s+(?:access|use)\s+(?:the\s+)?network", re.I),
     "network", ""),
    (re.compile(r"(?:may|can|allowed?\s+to)\s+(?:write|create|modify)\s+files?", re.I),
     "filesystem", "write"),
]

_GATE_HEURISTIC_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(?:ask|confirm|approval|human.+review).+(?:before|prior)", re.I),
     "ask_confirmation"),
    (re.compile(r"(?:before).+(?:ask|confirm|approval|human.+review)", re.I),
     "ask_confirmation"),
    (re.compile(r"require.+(?:human|manual|user).+(?:approval|confirmation|review)", re.I),
     "ask_confirmation"),
    (re.compile(r"(?:sensitive|dangerous|destructive|irreversible).+(?:confirm|approv)", re.I),
     "ask_confirmation"),
]

_GOAL_HEADING_KEYWORDS = {"goal", "objective", "purpose", "mission", "overview"}
_CONSTRAINT_HEADING_KEYWORDS = {
    "constraint", "rule", "restriction", "limitation", "boundary",
    "guideline", "requirement", "safety", "do not", "don't",
}


def import_instruction_markdown(text: str) -> dict[str, Any]:
    """Parse an AGENTS.md or CLAUDE.md document and return a draft GovernSpec dict."""
    text = strip_frontmatter(text)
    sections = split_sections(text)

    if _is_governspec_generated(sections):
        return _parse_governspec_generated(sections)
    return _parse_handwritten(text, sections)


def _is_governspec_generated(sections: dict[str, str]) -> bool:
    return len(_INTENTSPEC_GENERATED_SECTIONS & set(sections.keys())) >= 4


def _parse_governspec_generated(sections: dict[str, str]) -> dict[str, Any]:
    goal = sections.get("Project Goal", "").strip()
    if not goal:
        raise GovernSpecParseError(
            "Could not find 'Project Goal' section in instruction document.",
            suggestion="Ensure the document has a '## Project Goal' section.",
        )

    constraints = extract_items(sections.get("Working Constraints", ""))
    permissions = parse_permissions(sections.get("Allowed and Forbidden Operations", ""))
    human_gates = parse_human_gates(sections.get("Human Confirmation Rules", ""))
    output_spec = parse_output(sections.get("Output Expectations", ""))
    verification = extract_items(sections.get("Verification Steps", ""))

    title_match = _H1_RE.search(
        sections.get("Project Goal", "") + sections.get("Working Constraints", "")
    )
    title = ""
    if title_match:
        title = title_match.group(1).strip()

    return build_draft_payload(
        goal=goal,
        constraints=constraints,
        permissions=permissions,
        human_gates=human_gates,
        output_spec=output_spec,
        tests=build_verification_tests(verification),
        title=title,
    )


def _parse_handwritten(full_text: str, sections: dict[str, str]) -> dict[str, Any]:
    """Heuristic import for hand-written markdown instruction documents."""
    goal = _infer_goal(full_text, sections)
    if not goal:
        raise GovernSpecParseError(
            "Could not extract a goal from the instruction document.",
            suggestion=(
                "Add a '## Goal' or '## Project Goal' section, or ensure the "
                "document has a clear top-level heading."
            ),
        )

    constraints = _infer_constraints(sections)
    permissions = _infer_permissions(full_text)
    human_gates = _infer_human_gates(full_text)
    output_spec = _infer_output(sections)
    tests = _infer_tests(sections)

    h1_match = _H1_RE.search(full_text)
    title = h1_match.group(1).strip() if h1_match else ""

    return build_draft_payload(
        goal=goal,
        constraints=constraints,
        permissions=permissions,
        human_gates=human_gates,
        output_spec=output_spec,
        tests=tests,
        title=title,
    )


def _infer_goal(full_text: str, sections: dict[str, str]) -> str:
    for heading, body in sections.items():
        if any(kw in heading.lower() for kw in _GOAL_HEADING_KEYWORDS):
            text = body.strip()
            items = extract_items(text)
            if items:
                return items[0]
            first_line = text.split("\n", 1)[0].strip()
            if first_line:
                return first_line

    h1_match = _H1_RE.search(full_text)
    if h1_match:
        candidate = h1_match.group(1).strip()
        if candidate.lower() not in {"agents.md", "claude.md"}:
            return candidate

    for heading, body in sections.items():
        heading_lower = heading.lower()
        if any(kw in heading_lower for kw in _CONSTRAINT_HEADING_KEYWORDS):
            continue
        text = body.strip()
        first_line = text.split("\n", 1)[0].strip()
        if first_line and len(first_line) > 10:
            return first_line

    return ""


def _infer_constraints(sections: dict[str, str]) -> list[str]:
    constraints: list[str] = []

    for heading, body in sections.items():
        heading_lower = heading.lower()
        if any(kw in heading_lower for kw in _CONSTRAINT_HEADING_KEYWORDS):
            constraints.extend(extract_items(body))
            continue

    if not constraints:
        for _heading, body in sections.items():
            for item in extract_items(body):
                lowered = item.lower()
                if any(phrase in lowered for phrase in (
                    "do not", "don't", "never", "must not", "forbidden",
                    "prohibited", "avoid", "disallowed",
                )):
                    constraints.append(item)

    return constraints


def _infer_permissions(full_text: str) -> dict[str, Any]:
    permissions = default_permissions()

    for pattern, group, subkey in _PERMISSION_DENY_PATTERNS:
        if pattern.search(full_text):
            if subkey:
                permissions[group][subkey] = False
            else:
                permissions[group] = False

    for pattern, group, subkey in _PERMISSION_ALLOW_PATTERNS:
        if pattern.search(full_text):
            if subkey:
                permissions[group][subkey] = True
            else:
                permissions[group] = True

    return permissions


def _infer_human_gates(full_text: str) -> list[dict[str, str]]:
    gates: list[dict[str, str]] = []
    seen_triggers: set[str] = set()

    for line in full_text.splitlines():
        stripped = line.strip().lstrip("- ")
        if not stripped:
            continue
        for pattern, action in _GATE_HEURISTIC_PATTERNS:
            if pattern.search(stripped) and stripped not in seen_triggers:
                seen_triggers.add(stripped)
                gates.append({"when": stripped, "action": action})
                break

    return gates


def _infer_output(sections: dict[str, str]) -> dict[str, Any]:
    for heading, body in sections.items():
        heading_lower = heading.lower()
        if "output" in heading_lower or "format" in heading_lower:
            items = extract_items(body)
            if items:
                sections_list = [
                    item for item in items
                    if not any(kw in item.lower() for kw in (
                        "format", "language", "max word", "json schema",
                    ))
                ]
                return {
                    "format": "markdown",
                    "language": "en",
                    "max_words": 500,
                    "sections": sections_list or ["Summary"],
                }

    return {
        "format": "markdown",
        "language": "en",
        "max_words": 500,
        "sections": ["Summary"],
    }


def _infer_tests(sections: dict[str, str]) -> list[dict[str, Any]]:
    for heading, body in sections.items():
        heading_lower = heading.lower()
        if any(kw in heading_lower for kw in ("verif", "test", "check", "accept")):
            items = extract_items(body)
            if items:
                return build_verification_tests(items)

    return [
        {"name": "Must include all sections", "assert": [{"type": "required_sections"}]}
    ]
