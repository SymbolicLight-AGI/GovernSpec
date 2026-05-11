from __future__ import annotations

from pathlib import Path

from governspec_core.imports.resolver import resolve_imports
from governspec_core.spec.parser import load_spec


def test_same_named_imported_tests_merge_assertions_instead_of_overriding(
    tmp_path: Path,
) -> None:
    pack_file = tmp_path / "policy.govern.yaml"
    spec_file = tmp_path / "task.govern.yaml"

    pack_file.write_text(
        """
version: "0.1"
kind: "GovernPack"

metadata:
  name: "policy_pack"

tests:
  - name: "PII guard"
    assert:
      - type: "not_contains"
        value: "SSN"
""".strip(),
        encoding="utf-8",
    )
    spec_file.write_text(
        f"""
version: "0.1"
kind: "GovernSpec"

imports:
  - "./{pack_file.name}"

metadata:
  name: "task"

task:
  goal: "Summarize the input"

output:
  format: "markdown"
  language: "en"
  max_words: 200
  sections:
    - "Summary"

tests:
  - name: "PII guard"
    assert:
      - type: "not_contains"
        value: "SSN"
      - type: "required_sections"
""".strip(),
        encoding="utf-8",
    )

    resolved = resolve_imports(load_spec(spec_file))

    assert len(resolved.tests) == 1
    merged_test = resolved.tests[0]
    assert merged_test.name == "PII guard"
    assert [assertion.type for assertion in merged_test.assertions] == [
        "not_contains",
        "required_sections",
    ]
