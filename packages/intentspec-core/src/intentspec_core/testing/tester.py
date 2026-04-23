"""Acceptance testing for IntentSpec outputs."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from typing import Any

from jsonschema import ValidationError as JsonSchemaValidationError  # type: ignore[import-untyped]
from jsonschema import validate as validate_json_schema  # type: ignore[import-untyped]

from intentspec_core.common.utils import (
    estimate_word_count,
    find_json_path,
    format_count,
)
from intentspec_core.spec.models import Assertion, IntentSpec, JsonOutput

REGEX_ASSERTION_TIMEOUT_SECONDS = 2.0
_REGEX_SEARCH_SCRIPT = """
import json
import re
import sys

payload = json.load(sys.stdin)
matched = re.search(
    payload["pattern"],
    payload["output_text"],
    flags=re.MULTILINE,
) is not None
json.dump({"matched": matched}, sys.stdout)
""".strip()


@dataclass(slots=True)
class TestReport:
    ok: bool
    passed: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_text(self) -> str:
        lines = [f"Test status: {'ok' if self.ok else 'failed'}"]
        if self.passed:
            lines.append("Passed:")
            lines.extend(f"- {item}" for item in self.passed)
        else:
            lines.append("Passed: none")
        if self.failed:
            lines.append("Failed assertions:")
            lines.extend(f"- {item}" for item in self.failed)
        else:
            lines.append("Failed: none")
        if self.warnings:
            lines.append("Warnings:")
            lines.extend(f"- {item}" for item in self.warnings)
        else:
            lines.append("Warnings: none")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def test_output(spec: IntentSpec, output_text: str) -> TestReport:
    passed: list[str] = []
    failed: list[str] = []
    warnings: list[str] = []
    parsed_json: Any | None = None

    if not spec.tests:
        warnings.append("Spec defines no tests.")

    if isinstance(spec.output, JsonOutput):
        try:
            parsed_json = json.loads(output_text)
        except json.JSONDecodeError as exc:
            failed.append(f"JSON output: Invalid JSON at line {exc.lineno}, column {exc.colno}.")
            return TestReport(ok=False, passed=passed, failed=failed, warnings=warnings)

    for test_case in spec.tests:
        for assertion in test_case.assertions:
            success, message = _evaluate_assertion(spec, output_text, parsed_json, assertion)
            label = f"{test_case.name} [{assertion.type}]"
            if success:
                passed.append(f"{label}: {message}")
            else:
                failed.append(f"{label}: {message}")

    return TestReport(ok=not failed, passed=passed, failed=failed, warnings=warnings)


setattr(test_output, "__test__", False)


def _evaluate_assertion(
    spec: IntentSpec,
    output_text: str,
    parsed_json: Any | None,
    assertion: Assertion,
) -> tuple[bool, str]:
    assertion_type = assertion.type.strip()

    if assertion_type == "required_sections":
        missing_sections = [
            section
            for section in getattr(spec.output, "sections", [])
            if not _section_present(output_text, section)
        ]
        if missing_sections:
            return False, f"Missing sections: {', '.join(missing_sections)}"
        return True, "All required sections are present."

    if assertion_type == "contains":
        if not isinstance(assertion.value, str):
            return False, "Assertion requires a string value."
        if assertion.value in output_text:
            return True, f'Found required text: "{assertion.value}"'
        return False, f'Missing required text: "{assertion.value}"'

    if assertion_type == "not_contains":
        if not isinstance(assertion.value, str):
            return False, "Assertion requires a string value."
        if assertion.value in output_text:
            return False, f'Found forbidden text: "{assertion.value}"'
        return True, f'Forbidden text absent: "{assertion.value}"'

    if assertion_type == "regex":
        return _evaluate_regex_assertion(output_text, assertion.pattern, should_match=True)

    if assertion_type == "no_regex":
        return _evaluate_regex_assertion(output_text, assertion.pattern, should_match=False)

    if assertion_type == "max_words":
        word_limit = getattr(spec.output, "max_words", None)
        if word_limit is None:
            return False, "Assertion requires output.max_words for the current output format."
        word_count = estimate_word_count(output_text)
        if word_count <= word_limit:
            return True, (
                f"Estimated word count {format_count(word_count)} is within limit {word_limit}."
            )
        return False, (
            f"Estimated word count {format_count(word_count)} exceeds limit {word_limit}."
        )

    if assertion_type == "max_chars":
        if not isinstance(assertion.value, int):
            return False, "Assertion requires an integer value."
        char_count = len(output_text)
        if char_count <= assertion.value:
            return True, f"Character count {char_count} is within limit {assertion.value}."
        return False, f"Character count {char_count} exceeds limit {assertion.value}."

    if assertion_type == "json_schema":
        if parsed_json is None:
            return False, "Assertion requires JSON output."
        schema = getattr(spec.output, "json_schema", None)
        if not isinstance(schema, dict):
            return False, "Assertion requires output.schema."
        try:
            validate_json_schema(parsed_json, schema)
        except JsonSchemaValidationError as exc:
            return False, f"JSON schema validation failed: {exc.message}"
        return True, "JSON output matches output.schema."

    if assertion_type == "json_path_exists":
        if parsed_json is None:
            return False, "Assertion requires JSON output."
        if not assertion.path:
            return False, "Assertion requires a JSON path."
        found, _ = find_json_path(parsed_json, assertion.path)
        if found:
            return True, f"JSON path exists: {assertion.path}"
        return False, f"JSON path not found: {assertion.path}"

    if assertion_type == "json_array_min_items":
        if parsed_json is None:
            return False, "Assertion requires JSON output."
        if not assertion.path:
            return False, "Assertion requires a JSON path."
        if not isinstance(assertion.value, int):
            return False, "Assertion requires an integer value."
        found, payload = find_json_path(parsed_json, assertion.path)
        if not found:
            return False, f"JSON path not found: {assertion.path}"
        if not isinstance(payload, list):
            return False, f"JSON path is not an array: {assertion.path}"
        if len(payload) >= assertion.value:
            return True, (
                f"JSON array at {assertion.path} has {len(payload)} items, "
                f"meets minimum {assertion.value}."
            )
        return False, (
            f"JSON array at {assertion.path} has {len(payload)} items, "
            f"below minimum {assertion.value}."
        )

    return False, f"Unknown assertion type: {assertion.type}"


def _evaluate_regex_assertion(
    output_text: str, pattern: str | None, *, should_match: bool
) -> tuple[bool, str]:
    if not pattern:
        return False, "Assertion requires a regex pattern."

    matched, error_message = _run_regex_match(pattern, output_text)
    if error_message is not None:
        return False, error_message

    if should_match and matched:
        return True, f'Regex matched pattern: "{pattern}"'
    if should_match and not matched:
        return False, f'Regex did not match pattern: "{pattern}"'
    if not should_match and matched:
        return False, f'Regex matched forbidden pattern: "{pattern}"'
    return True, f'Regex did not match forbidden pattern: "{pattern}"'


def _run_regex_match(pattern: str, output_text: str) -> tuple[bool, str | None]:
    try:
        re.compile(pattern)
    except re.error as exc:
        return False, f"Invalid regex pattern: {exc}"

    try:
        completed = subprocess.run(
            [sys.executable, "-c", _REGEX_SEARCH_SCRIPT],
            input=json.dumps(
                {"pattern": pattern, "output_text": output_text},
                ensure_ascii=False,
            ),
            capture_output=True,
            check=False,
            text=True,
            timeout=REGEX_ASSERTION_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return (
            False,
            "Regex evaluation timed out after "
            f"{format_count(REGEX_ASSERTION_TIMEOUT_SECONDS)} seconds.",
        )

    if completed.returncode != 0:
        return False, "Regex evaluation failed."

    try:
        matched = bool(json.loads(completed.stdout)["matched"])
    except (json.JSONDecodeError, KeyError, TypeError):
        return False, "Regex evaluation failed."

    return matched, None


def _section_present(output_text: str, section: str) -> bool:
    heading_pattern = re.compile(rf"(?mi)^\s{{0,3}}#{1,6}\s*{re.escape(section)}\s*$")
    if heading_pattern.search(output_text):
        return True
    return section in output_text
