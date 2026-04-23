"""Import a Cursor Rules .mdc file into an IntentSpec draft."""

from __future__ import annotations

from typing import Any

from intentspec_core.common.errors import IntentSpecParseError
from intentspec_core.importers._parsing import (
    build_draft_payload,
    build_verification_tests,
    extract_items,
    parse_human_gates,
    parse_output,
    parse_permissions,
    split_sections,
    strip_frontmatter,
)


def import_cursor_rules(text: str) -> dict[str, Any]:
    """Parse a Cursor Rules .mdc document and return a draft IntentSpec dict."""
    body = strip_frontmatter(text)
    sections = split_sections(body)

    goal = sections.get("Project Goal", "").strip()
    if not goal:
        raise IntentSpecParseError(
            "Could not find 'Project Goal' section in cursor-rules document.",
            suggestion="Ensure the .mdc file has a '## Project Goal' section.",
        )

    constraints = extract_items(sections.get("Working Constraints", ""))
    permissions = parse_permissions(sections.get("Allowed and Forbidden Operations", ""))
    human_gates = parse_human_gates(sections.get("Human Confirmation Rules", ""))
    output_spec = parse_output(sections.get("Output Expectations", ""))
    verification = extract_items(sections.get("Verification Steps", ""))

    return build_draft_payload(
        goal=goal,
        constraints=constraints,
        permissions=permissions,
        human_gates=human_gates,
        output_spec=output_spec,
        tests=build_verification_tests(verification),
    )
