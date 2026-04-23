from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from intentspec.cli import app
from intentspec_core.common.errors import IntentSpecParseError
from intentspec_core.importers.cursor_rules import import_cursor_rules
from intentspec_core.importers.gemini_structured import import_gemini_structured
from intentspec_core.importers.instruction_markdown import import_instruction_markdown
from intentspec_core.importers.openai_structured import import_openai_structured
from intentspec_core.importers.reverse import (
    SUPPORTED_IMPORT_TYPES,
    import_from_artifact,
    import_from_string,
)
from intentspec_core.imports.resolver import resolve_imports
from intentspec_core.spec.parser import load_spec
from intentspec_core.targets.compiler import compile_target
from intentspec_core.validator import validate_spec
from typer.testing import CliRunner

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
runner = CliRunner()


# ---------------------------------------------------------------------------
# OpenAI Structured
# ---------------------------------------------------------------------------


def test_openai_structured_import_extracts_schema() -> None:
    payload = {
        "type": "json_schema",
        "json_schema": {
            "name": "report_json",
            "description": "Produce a strict JSON report.",
            "strict": True,
            "schema": {
                "type": "object",
                "required": ["verdict", "risks"],
                "properties": {
                    "verdict": {"type": "string"},
                    "risks": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
    }
    result = import_openai_structured(payload)
    assert result["version"] == "0.1"
    assert result["kind"] == "IntentSpec"
    assert result["metadata"]["name"] == "report_json"
    assert result["output"]["format"] == "json"
    assert result["output"]["schema"]["required"] == ["verdict", "risks"]


def test_openai_structured_import_generates_tests() -> None:
    payload = {
        "type": "json_schema",
        "json_schema": {
            "name": "test_output",
            "description": "Test",
            "strict": True,
            "schema": {
                "type": "object",
                "required": ["a", "b"],
                "properties": {"a": {"type": "string"}, "b": {"type": "string"}},
            },
        },
    }
    result = import_openai_structured(payload)
    test_names = [t["name"] for t in result["tests"]]
    assert "Must match JSON schema" in test_names
    assert "Field 'a' must exist" in test_names
    assert "Field 'b' must exist" in test_names


def test_openai_structured_import_rejects_missing_json_schema_key() -> None:
    with pytest.raises(IntentSpecParseError):
        import_openai_structured({"type": "json_schema"})


def test_openai_structured_import_rejects_empty_schema() -> None:
    with pytest.raises(IntentSpecParseError):
        import_openai_structured(
            {"type": "json_schema", "json_schema": {"name": "x", "schema": {}}}
        )


# ---------------------------------------------------------------------------
# Gemini Structured
# ---------------------------------------------------------------------------


def test_gemini_structured_import_extracts_schema() -> None:
    payload = {
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseJsonSchema": {
                "type": "object",
                "required": ["verdict"],
                "properties": {"verdict": {"type": "string"}},
            },
        }
    }
    result = import_gemini_structured(payload)
    assert result["version"] == "0.1"
    assert result["kind"] == "IntentSpec"
    assert result["output"]["format"] == "json"
    assert result["output"]["schema"]["required"] == ["verdict"]


def test_gemini_structured_import_rejects_missing_config() -> None:
    with pytest.raises(IntentSpecParseError):
        import_gemini_structured({})


def test_gemini_structured_import_rejects_empty_schema() -> None:
    with pytest.raises(IntentSpecParseError):
        import_gemini_structured({"generationConfig": {"responseJsonSchema": {}}})


# ---------------------------------------------------------------------------
# Cursor Rules
# ---------------------------------------------------------------------------


SAMPLE_CURSOR_RULES = """\
---
description: IntentSpec-generated project rules
alwaysApply: true
---

# IntentSpec Cursor Rules

## Project Goal
Review the codebase and summarize defects, risks, and follow-up tests.

## Working Constraints
- Do not directly modify code.
- Do not delete files.

## Allowed and Forbidden Operations
- Web access: forbidden
- Network access: forbidden
- Filesystem read: allowed
- Filesystem write: forbidden
- Tool send_email: forbidden
- Tool read_calendar: forbidden
- Tool read_gmail: forbidden
- Tool create_file: forbidden
- Tool delete_file: forbidden
- Tool purchase: forbidden

## Human Confirmation Rules
- none

## Output Expectations
- Format: markdown
- Language: en
- Max words: 900
- Section: Overall Assessment
- Section: Must Fix

## Verification Steps
- All sections must be present
"""


def test_cursor_rules_import_extracts_goal() -> None:
    result = import_cursor_rules(SAMPLE_CURSOR_RULES)
    assert result["task"]["goal"] == (
        "Review the codebase and summarize defects, risks, and follow-up tests."
    )


def test_cursor_rules_import_extracts_constraints() -> None:
    result = import_cursor_rules(SAMPLE_CURSOR_RULES)
    assert "Do not directly modify code." in result["constraints"]
    assert "Do not delete files." in result["constraints"]


def test_cursor_rules_import_extracts_permissions() -> None:
    result = import_cursor_rules(SAMPLE_CURSOR_RULES)
    permissions = result["permissions"]
    assert permissions["web"] is False
    assert permissions["network"] is False
    assert permissions["filesystem"]["read"] is True
    assert permissions["filesystem"]["write"] is False
    assert permissions["tools"]["send_email"] is False


def test_cursor_rules_import_extracts_output() -> None:
    result = import_cursor_rules(SAMPLE_CURSOR_RULES)
    output = result["output"]
    assert output["format"] == "markdown"
    assert output["language"] == "en"
    assert output["max_words"] == 900
    assert "Overall Assessment" in output["sections"]
    assert "Must Fix" in output["sections"]


def test_cursor_rules_import_extracts_verification_tests() -> None:
    result = import_cursor_rules(SAMPLE_CURSOR_RULES)
    assert any(t["name"] == "All sections must be present" for t in result["tests"])


def test_cursor_rules_import_parses_human_gates() -> None:
    text = """\
---
description: test
alwaysApply: true
---

# Test Rules

## Project Goal
Do something sensitive.

## Working Constraints
- Be careful.

## Allowed and Forbidden Operations
- Web access: forbidden

## Human Confirmation Rules
- Task involves privacy-sensitive information -> ask_confirmation
- High-risk action is required -> ask_confirmation

## Output Expectations
- Format: markdown
- Language: en
- Max words: 500
- Section: Summary

## Verification Steps
- Check result
"""
    result = import_cursor_rules(text)
    assert len(result["human_gates"]) == 2
    assert result["human_gates"][0]["when"] == "Task involves privacy-sensitive information"
    assert result["human_gates"][0]["action"] == "ask_confirmation"


def test_cursor_rules_import_rejects_missing_goal() -> None:
    text = """\
# No Goal Here

## Working Constraints
- Something
"""
    with pytest.raises(IntentSpecParseError):
        import_cursor_rules(text)


# ---------------------------------------------------------------------------
# Reverse unified entry point
# ---------------------------------------------------------------------------


def test_import_from_artifact_auto_detects_openai(tmp_path: Path) -> None:
    source = tmp_path / "structured.json"
    payload = {
        "type": "json_schema",
        "json_schema": {
            "name": "auto_detect",
            "description": "Auto",
            "strict": True,
            "schema": {
                    "type": "object",
                    "required": ["x"],
                    "properties": {"x": {"type": "string"}},
                },
        },
    }
    source.write_text(json.dumps(payload), encoding="utf-8")
    result = import_from_artifact(source)
    assert result["metadata"]["name"] == "auto_detect"


def test_import_from_artifact_auto_detects_gemini(tmp_path: Path) -> None:
    source = tmp_path / "gemini.json"
    payload = {
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseJsonSchema": {
                "type": "object",
                "required": ["y"],
                "properties": {"y": {"type": "string"}},
            },
        }
    }
    source.write_text(json.dumps(payload), encoding="utf-8")
    result = import_from_artifact(source)
    assert result["output"]["schema"]["required"] == ["y"]


def test_import_from_artifact_auto_detects_cursor_rules(tmp_path: Path) -> None:
    source = tmp_path / "rules.mdc"
    source.write_text(SAMPLE_CURSOR_RULES, encoding="utf-8")
    result = import_from_artifact(source)
    assert "Review the codebase" in result["task"]["goal"]


def test_import_from_string_works_for_all_types() -> None:
    openai_json = json.dumps({
        "type": "json_schema",
        "json_schema": {
            "name": "str_test",
            "description": "",
            "strict": True,
            "schema": {"type": "object", "properties": {"a": {"type": "string"}}},
        },
    })
    result = import_from_string(openai_json, "openai-structured")
    assert result["metadata"]["name"] == "str_test"

    result2 = import_from_string(SAMPLE_CURSOR_RULES, "cursor-rules")
    assert result2["kind"] == "IntentSpec"


def test_import_from_artifact_rejects_unsupported_type(tmp_path: Path) -> None:
    source = tmp_path / "unknown.txt"
    source.write_text("hello", encoding="utf-8")
    with pytest.raises(IntentSpecParseError):
        import_from_artifact(source)


def test_supported_import_types_includes_markdown() -> None:
    assert len(SUPPORTED_IMPORT_TYPES) >= 5
    assert "openai-structured" in SUPPORTED_IMPORT_TYPES
    assert "gemini-structured" in SUPPORTED_IMPORT_TYPES
    assert "cursor-rules" in SUPPORTED_IMPORT_TYPES
    assert "agents-md" in SUPPORTED_IMPORT_TYPES
    assert "claude-md" in SUPPORTED_IMPORT_TYPES


# ---------------------------------------------------------------------------
# Instruction Markdown (AGENTS.md / CLAUDE.md) — IntentSpec-generated
# ---------------------------------------------------------------------------


SAMPLE_AGENTS_MD = """\
# AGENTS.md

## Project Goal
Generate a customer brief using reusable governance packs.

## Working Constraints
- Do not expose private or personal data.
- Do not make pricing commitments.

## Allowed and Forbidden Operations
- Web access: forbidden
- Network access: forbidden
- Filesystem read: allowed
- Filesystem write: forbidden
- Tool send_email: forbidden
- Tool read_calendar: forbidden
- Tool read_gmail: forbidden
- Tool create_file: forbidden
- Tool delete_file: forbidden
- Tool purchase: forbidden

## Human Confirmation Rules
- Task involves privacy-sensitive information -> ask_confirmation

## Output Expectations
- Format: markdown
- Language: zh-CN
- Max words: 800
- Section: 一句话结论
- Section: 客户背景
- Section: 风险信号

## Verification Steps
- Must not leak phone numbers
- All sections must be present
"""


SAMPLE_CLAUDE_MD = """\
# CLAUDE.md

## Project Goal
Review the codebase and summarize defects, risks, and follow-up tests.

## Working Constraints
- Do not directly modify code.

## Allowed and Forbidden Operations
- Web access: forbidden
- Network access: forbidden
- Filesystem read: allowed
- Filesystem write: forbidden
- Tool send_email: forbidden
- Tool read_calendar: forbidden
- Tool read_gmail: forbidden
- Tool create_file: forbidden
- Tool delete_file: forbidden
- Tool purchase: forbidden

## Human Confirmation Rules
- none

## Output Expectations
- Format: markdown
- Language: en
- Max words: 900
- Section: Overall Assessment
- Section: Must Fix

## Verification Steps
- All sections must be present
"""


def test_instruction_md_import_extracts_goal() -> None:
    result = import_instruction_markdown(SAMPLE_AGENTS_MD)
    assert result["task"]["goal"] == (
        "Generate a customer brief using reusable governance packs."
    )


def test_instruction_md_import_extracts_constraints() -> None:
    result = import_instruction_markdown(SAMPLE_AGENTS_MD)
    assert "Do not expose private or personal data." in result["constraints"]
    assert "Do not make pricing commitments." in result["constraints"]


def test_instruction_md_import_extracts_permissions() -> None:
    result = import_instruction_markdown(SAMPLE_AGENTS_MD)
    p = result["permissions"]
    assert p["web"] is False
    assert p["filesystem"]["read"] is True
    assert p["filesystem"]["write"] is False
    assert p["tools"]["send_email"] is False


def test_instruction_md_import_extracts_human_gates() -> None:
    result = import_instruction_markdown(SAMPLE_AGENTS_MD)
    assert len(result["human_gates"]) == 1
    assert result["human_gates"][0]["when"] == (
        "Task involves privacy-sensitive information"
    )
    assert result["human_gates"][0]["action"] == "ask_confirmation"


def test_instruction_md_import_extracts_output() -> None:
    result = import_instruction_markdown(SAMPLE_AGENTS_MD)
    output = result["output"]
    assert output["format"] == "markdown"
    assert output["language"] == "zh-CN"
    assert output["max_words"] == 800
    assert "一句话结论" in output["sections"]
    assert "客户背景" in output["sections"]
    assert "风险信号" in output["sections"]


def test_instruction_md_import_extracts_verification() -> None:
    result = import_instruction_markdown(SAMPLE_AGENTS_MD)
    test_names = [t["name"] for t in result["tests"]]
    assert "Must not leak phone numbers" in test_names
    assert "All sections must be present" in test_names


def test_instruction_md_claude_format() -> None:
    result = import_instruction_markdown(SAMPLE_CLAUDE_MD)
    assert "Review the codebase" in result["task"]["goal"]
    assert result["output"]["language"] == "en"
    assert result["output"]["max_words"] == 900
    assert "Overall Assessment" in result["output"]["sections"]


def test_instruction_md_json_output_format() -> None:
    text = """\
# AGENTS.md

## Project Goal
Generate structured JSON report.

## Working Constraints
- Do not fabricate evidence.

## Allowed and Forbidden Operations
- Web access: forbidden
- Network access: forbidden
- Filesystem read: allowed
- Filesystem write: forbidden
- Tool send_email: forbidden
- Tool read_calendar: forbidden
- Tool read_gmail: forbidden
- Tool create_file: forbidden
- Tool delete_file: forbidden
- Tool purchase: forbidden

## Human Confirmation Rules
- none

## Output Expectations
- Format: json
- JSON Schema is required.

## Verification Steps
- JSON must match schema
"""
    result = import_instruction_markdown(text)
    assert result["output"]["format"] == "json"
    assert "schema" in result["output"]


# ---------------------------------------------------------------------------
# Instruction Markdown — Hand-written (heuristic parsing)
# ---------------------------------------------------------------------------


HANDWRITTEN_AGENTS_MD = """\
# Project Code Review Agent

## Goal
Audit the repository for security vulnerabilities and code quality issues.

## Rules
- Do not modify any source files.
- Do not access the web or internet.
- Do not send emails.
- Never delete files or directories.

## Output
- Security Issues
- Code Quality
- Recommendations

## Testing
- All sections present
- No false positives
"""


def test_handwritten_md_extracts_goal() -> None:
    result = import_instruction_markdown(HANDWRITTEN_AGENTS_MD)
    assert "security vulnerabilities" in result["task"]["goal"].lower()


def test_handwritten_md_extracts_constraints_from_rules() -> None:
    result = import_instruction_markdown(HANDWRITTEN_AGENTS_MD)
    assert any("modify" in c.lower() for c in result["constraints"])


def test_handwritten_md_infers_permissions() -> None:
    result = import_instruction_markdown(HANDWRITTEN_AGENTS_MD)
    p = result["permissions"]
    assert p["web"] is False
    assert p["tools"]["send_email"] is False
    assert p["tools"]["delete_file"] is False


def test_handwritten_md_extracts_output_sections() -> None:
    result = import_instruction_markdown(HANDWRITTEN_AGENTS_MD)
    output = result["output"]
    assert "Security Issues" in output["sections"]
    assert "Code Quality" in output["sections"]
    assert "Recommendations" in output["sections"]


def test_handwritten_md_extracts_tests() -> None:
    result = import_instruction_markdown(HANDWRITTEN_AGENTS_MD)
    test_names = [t["name"] for t in result["tests"]]
    assert "All sections present" in test_names
    assert "No false positives" in test_names


def test_handwritten_md_with_human_gates() -> None:
    text = """\
# Deploy Agent

## Purpose
Deploy the application to staging.

## Constraints
- Require human approval before pushing to production.
- Ask confirmation before running destructive operations.
- Do not modify production databases without review.

## Checks
- Deployment succeeded
"""
    result = import_instruction_markdown(text)
    assert len(result["human_gates"]) >= 1
    actions = [g["action"] for g in result["human_gates"]]
    assert "ask_confirmation" in actions


def test_handwritten_md_minimal() -> None:
    text = """\
# Quick Analysis

## Objective
Summarize the quarterly sales data.

## Notes
- Use only provided data files.
- Do not fabricate numbers.
"""
    result = import_instruction_markdown(text)
    assert "quarterly sales" in result["task"]["goal"].lower()
    assert result["kind"] == "IntentSpec"
    assert result["version"] == "0.1"


def test_handwritten_md_with_filesystem_write_allowed() -> None:
    text = """\
# File Generator

## Goal
Generate report files in the output directory.

## Rules
- May write files to the output directory.
- Do not access the internet.
"""
    result = import_instruction_markdown(text)
    assert result["permissions"]["filesystem"]["write"] is True
    assert result["permissions"]["web"] is False


def test_handwritten_md_rejects_empty_goal() -> None:
    text = """\
## Constraints
- Do not fabricate data.

## Rules
- Be precise.
"""
    with pytest.raises(IntentSpecParseError):
        import_instruction_markdown(text)


# ---------------------------------------------------------------------------
# Reverse entry: auto-detection and import_from_string for markdown
# ---------------------------------------------------------------------------


def test_import_from_artifact_auto_detects_agents_md(tmp_path: Path) -> None:
    source = tmp_path / "AGENTS.md"
    source.write_text(SAMPLE_AGENTS_MD, encoding="utf-8")
    result = import_from_artifact(source)
    assert "customer brief" in result["task"]["goal"].lower()


def test_import_from_artifact_auto_detects_claude_md(tmp_path: Path) -> None:
    source = tmp_path / "CLAUDE.md"
    source.write_text(SAMPLE_CLAUDE_MD, encoding="utf-8")
    result = import_from_artifact(source)
    assert "Review the codebase" in result["task"]["goal"]


def test_import_from_artifact_md_extension_auto_detect(tmp_path: Path) -> None:
    source = tmp_path / "instructions.md"
    source.write_text(HANDWRITTEN_AGENTS_MD, encoding="utf-8")
    result = import_from_artifact(source)
    assert result["kind"] == "IntentSpec"


def test_import_from_string_agents_md() -> None:
    result = import_from_string(SAMPLE_AGENTS_MD, "agents-md")
    assert result["kind"] == "IntentSpec"
    assert "customer brief" in result["task"]["goal"].lower()


def test_import_from_string_claude_md() -> None:
    result = import_from_string(SAMPLE_CLAUDE_MD, "claude-md")
    assert result["kind"] == "IntentSpec"
    assert "Review the codebase" in result["task"]["goal"]


# ---------------------------------------------------------------------------
# Round-trip: compile → import → validate
# ---------------------------------------------------------------------------


def test_roundtrip_openai_structured(tmp_path: Path) -> None:
    """Compile an intent to OpenAI structured, import it back, validate the result."""
    spec = load_spec(EXAMPLES / "report_json.intent.yaml")
    compiled = compile_target(spec, "openai-structured")
    assert compiled.content is not None

    source = tmp_path / "openai.json"
    source.write_text(compiled.content, encoding="utf-8")
    imported = import_from_artifact(source)

    draft_path = tmp_path / "recovered.intent.yaml"
    draft_path.write_text(
        yaml.safe_dump(imported, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    recovered = resolve_imports(load_spec(draft_path))
    report = validate_spec(recovered)
    assert report.ok, f"Validation failed: {report.errors}"


def test_roundtrip_gemini_structured(tmp_path: Path) -> None:
    """Compile an intent to Gemini structured, import it back, validate the result."""
    spec = load_spec(EXAMPLES / "report_json.intent.yaml")
    compiled = compile_target(spec, "gemini-structured")
    assert compiled.content is not None

    source = tmp_path / "gemini.json"
    source.write_text(compiled.content, encoding="utf-8")
    imported = import_from_artifact(source)

    draft_path = tmp_path / "recovered.intent.yaml"
    draft_path.write_text(
        yaml.safe_dump(imported, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    recovered = resolve_imports(load_spec(draft_path))
    report = validate_spec(recovered)
    assert report.ok, f"Validation failed: {report.errors}"


def test_roundtrip_cursor_rules(tmp_path: Path) -> None:
    """Compile an intent to cursor-rules, import it back, validate the result."""
    spec = load_spec(EXAMPLES / "code_review.intent.yaml")
    compiled = compile_target(spec, "cursor-rules")
    mdc_content = compiled.files[".cursor/rules/intentspec.mdc"]

    imported = import_cursor_rules(mdc_content)

    draft_path = tmp_path / "recovered.intent.yaml"
    draft_path.write_text(
        yaml.safe_dump(imported, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    recovered = resolve_imports(load_spec(draft_path))
    report = validate_spec(recovered)
    assert report.ok, f"Validation failed: {report.errors}"


def test_roundtrip_agents_md(tmp_path: Path) -> None:
    """Compile to agents-md, import back, validate."""
    spec = load_spec(EXAMPLES / "code_review.intent.yaml")
    compiled = compile_target(spec, "agents-md")
    assert compiled.content is not None

    imported = import_instruction_markdown(compiled.content)

    draft_path = tmp_path / "recovered.intent.yaml"
    draft_path.write_text(
        yaml.safe_dump(imported, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    recovered = resolve_imports(load_spec(draft_path))
    report = validate_spec(recovered)
    assert report.ok, f"Validation failed: {report.errors}"


def test_roundtrip_claude_md(tmp_path: Path) -> None:
    """Compile to claude-md, import back, validate."""
    spec = load_spec(EXAMPLES / "code_review.intent.yaml")
    compiled = compile_target(spec, "claude-md")
    assert compiled.content is not None

    imported = import_instruction_markdown(compiled.content)

    draft_path = tmp_path / "recovered.intent.yaml"
    draft_path.write_text(
        yaml.safe_dump(imported, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    recovered = resolve_imports(load_spec(draft_path))
    report = validate_spec(recovered)
    assert report.ok, f"Validation failed: {report.errors}"


def test_roundtrip_agents_md_with_human_gates(tmp_path: Path) -> None:
    """Compile imported_customer_brief to agents-md and back — preserves gates."""
    spec = resolve_imports(
        load_spec(EXAMPLES / "imported_customer_brief.intent.yaml")
    )
    compiled = compile_target(spec, "agents-md")
    assert compiled.content is not None

    imported = import_instruction_markdown(compiled.content)

    assert len(imported["human_gates"]) >= 1
    assert imported["human_gates"][0]["action"] == "ask_confirmation"

    draft_path = tmp_path / "recovered.intent.yaml"
    draft_path.write_text(
        yaml.safe_dump(imported, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    recovered = resolve_imports(load_spec(draft_path))
    report = validate_spec(recovered)
    assert report.ok, f"Validation failed: {report.errors}"


def test_roundtrip_agents_md_json_output(tmp_path: Path) -> None:
    """Compile a JSON-output intent to agents-md and back."""
    spec = load_spec(EXAMPLES / "report_json.intent.yaml")
    compiled = compile_target(spec, "agents-md")
    assert compiled.content is not None

    imported = import_instruction_markdown(compiled.content)
    assert imported["output"]["format"] == "json"

    draft_path = tmp_path / "recovered.intent.yaml"
    draft_path.write_text(
        yaml.safe_dump(imported, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    recovered = resolve_imports(load_spec(draft_path))
    report = validate_spec(recovered)
    assert report.ok, f"Validation failed: {report.errors}"


# ---------------------------------------------------------------------------
# CLI: intent import
# ---------------------------------------------------------------------------


def test_import_cli_openai_structured(tmp_path: Path) -> None:
    source = tmp_path / "openai.json"
    spec = load_spec(EXAMPLES / "report_json.intent.yaml")
    compiled = compile_target(spec, "openai-structured")
    source.write_text(compiled.content or "", encoding="utf-8")

    out = tmp_path / "imported.intent.yaml"
    result = runner.invoke(
        app,
        ["import", str(source), "--type", "openai-structured", "--out", str(out)],
    )
    assert result.exit_code == 0
    assert out.exists()
    data = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert data["kind"] == "IntentSpec"
    assert data["output"]["format"] == "json"


def test_import_cli_auto_detect(tmp_path: Path) -> None:
    source = tmp_path / "auto.json"
    source.write_text(
        json.dumps({
            "type": "json_schema",
            "json_schema": {
                "name": "cli_auto",
                "description": "CLI auto-detect test",
                "strict": True,
                "schema": {
                    "type": "object",
                    "required": ["x"],
                    "properties": {"x": {"type": "string"}},
                },
            },
        }),
        encoding="utf-8",
    )
    result = runner.invoke(app, ["import", str(source)])
    assert result.exit_code == 0
    data = yaml.safe_load(result.stdout)
    assert data["metadata"]["name"] == "cli_auto"


def test_import_cli_refuses_overwrite(tmp_path: Path) -> None:
    source = tmp_path / "source.json"
    source.write_text(
        json.dumps({
            "type": "json_schema",
            "json_schema": {
                "name": "x",
                "description": "",
                "strict": True,
                "schema": {"type": "object", "properties": {"a": {"type": "string"}}},
            },
        }),
        encoding="utf-8",
    )
    out = tmp_path / "existing.yaml"
    out.write_text("already here", encoding="utf-8")
    result = runner.invoke(app, ["import", str(source), "--out", str(out)])
    assert result.exit_code == 1


def test_import_cli_agents_md(tmp_path: Path) -> None:
    source = tmp_path / "AGENTS.md"
    spec = load_spec(EXAMPLES / "code_review.intent.yaml")
    compiled = compile_target(spec, "agents-md")
    source.write_text(compiled.content or "", encoding="utf-8")

    out = tmp_path / "imported.intent.yaml"
    result = runner.invoke(
        app,
        ["import", str(source), "--type", "agents-md", "--out", str(out)],
    )
    assert result.exit_code == 0
    assert out.exists()
    data = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert data["kind"] == "IntentSpec"
    assert "Review the codebase" in data["task"]["goal"]


def test_import_cli_claude_md_auto_detect(tmp_path: Path) -> None:
    source = tmp_path / "CLAUDE.md"
    source.write_text(SAMPLE_CLAUDE_MD, encoding="utf-8")

    result = runner.invoke(app, ["import", str(source)])
    assert result.exit_code == 0
    data = yaml.safe_load(result.stdout)
    assert data["kind"] == "IntentSpec"


def test_import_cli_handwritten_md(tmp_path: Path) -> None:
    source = tmp_path / "instructions.md"
    source.write_text(HANDWRITTEN_AGENTS_MD, encoding="utf-8")

    out = tmp_path / "imported.intent.yaml"
    result = runner.invoke(
        app,
        ["import", str(source), "--out", str(out)],
    )
    assert result.exit_code == 0
    data = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert "security vulnerabilities" in data["task"]["goal"].lower()


def test_import_cli_rejects_bad_file(tmp_path: Path) -> None:
    source = tmp_path / "bad.txt"
    source.write_text("not json", encoding="utf-8")
    result = runner.invoke(app, ["import", str(source)])
    assert result.exit_code == 1
