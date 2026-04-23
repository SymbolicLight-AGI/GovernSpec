from __future__ import annotations

import json
from pathlib import Path

import pytest
from intentspec_core.common.errors import IntentSpecCompileError
from intentspec_core.imports.resolver import resolve_imports
from intentspec_core.spec.parser import load_spec
from intentspec_core.targets.compiler import compile_target

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def test_prompt_target_includes_goal_and_constraints() -> None:
    prompt = compile_target(
        resolve_imports(load_spec(EXAMPLES / "customer_brief.intent.yaml")),
        "prompt",
    )
    assert prompt.content is not None
    assert "## Goal" in prompt.content
    assert "## Constraints" in prompt.content


def test_openai_structured_target_is_valid_json() -> None:
    rendered = compile_target(load_spec(EXAMPLES / "report_json.intent.yaml"), "openai-structured")
    payload = json.loads(rendered.content or "")
    assert payload["type"] == "json_schema"
    assert payload["json_schema"]["strict"] is True


def test_agents_md_target_is_text() -> None:
    rendered = compile_target(load_spec(EXAMPLES / "code_review.intent.yaml"), "agents-md")
    assert rendered.content is not None
    assert "## Project Goal" in rendered.content
    assert "## Verification Steps" in rendered.content


def test_claude_md_target_is_text() -> None:
    rendered = compile_target(load_spec(EXAMPLES / "code_review.intent.yaml"), "claude-md")
    assert rendered.content is not None
    assert "# CLAUDE.md" in rendered.content
    assert "## Working Constraints" in rendered.content


def test_cursor_rules_target_returns_bundle() -> None:
    rendered = compile_target(load_spec(EXAMPLES / "code_review.intent.yaml"), "cursor-rules")
    assert rendered.kind == "bundle"
    assert ".cursor/rules/intentspec.mdc" in rendered.files
    assert "alwaysApply: true" in rendered.files[".cursor/rules/intentspec.mdc"]


def test_antigravity_rules_target_returns_bundle() -> None:
    rendered = compile_target(
        load_spec(EXAMPLES / "code_review.intent.yaml"),
        "antigravity-rules",
    )
    assert rendered.kind == "bundle"
    assert ".agents/rules/intentspec.md" in rendered.files
    assert "# IntentSpec Antigravity Rules" in rendered.files[".agents/rules/intentspec.md"]


def test_skill_target_returns_bundle() -> None:
    rendered = compile_target(load_spec(EXAMPLES / "code_review.intent.yaml"), "skill")
    assert rendered.kind == "bundle"
    assert "SKILL.md" in rendered.files
    assert "references/README.md" in rendered.files


def test_mcp_plan_target_contains_new_fields() -> None:
    rendered = compile_target(
        resolve_imports(load_spec(EXAMPLES / "imported_customer_brief.intent.yaml")),
        "mcp-plan",
    )
    payload = json.loads(rendered.content or "")
    assert payload["version"] == "0.1"
    assert "risk_level" in payload
    assert "required_user_consents" in payload
    assert "constraint_loss" in payload


def test_gemini_structured_target_is_valid_json() -> None:
    rendered = compile_target(load_spec(EXAMPLES / "report_json.intent.yaml"), "gemini-structured")
    payload = json.loads(rendered.content or "")
    assert payload["generationConfig"]["responseMimeType"] == "application/json"
    assert "responseJsonSchema" in payload["generationConfig"]


def test_gemini_structured_rejects_unsupported_schema_keywords(tmp_path: Path) -> None:
    spec_path = tmp_path / "unsupported.intent.yaml"
    spec_path.write_text(
        """
version: "0.1"
kind: "IntentSpec"

metadata:
  name: "unsupported_schema"
  title: "Unsupported schema"
  description: "Schema with oneOf"
  owner: "tests"

task:
  goal: "Return structured JSON."
  audience: []
  priority: "medium"

permissions:
  web: false
  filesystem:
    read: true
    write: false
  network: false
  tools:
    send_email: false
    read_calendar: false
    read_gmail: false
    create_file: false
    delete_file: false
    purchase: false

output:
  format: "json"
  schema:
    type: object
    properties:
      verdict:
        oneOf:
          - type: string
          - type: integer

tests:
  - name: "schema"
    assert:
      - type: "json_schema"
""".strip(),
        encoding="utf-8",
    )
    with pytest.raises(IntentSpecCompileError):
        compile_target(load_spec(spec_path), "gemini-structured")


def test_unsupported_target_raises_compile_error() -> None:
    with pytest.raises(IntentSpecCompileError):
        compile_target(load_spec(EXAMPLES / "customer_brief.intent.yaml"), "unknown-target")
