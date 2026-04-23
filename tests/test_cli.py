from __future__ import annotations

import json
from pathlib import Path

from intentspec.cli import app
from typer.testing import CliRunner

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
runner = CliRunner()


def test_validate_command_supports_json_format() -> None:
    result = runner.invoke(
        app,
        ["validate", str(EXAMPLES / "customer_brief.intent.yaml"), "--format", "json"],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True


def test_validate_command_supports_intent_pack() -> None:
    result = runner.invoke(
        app,
        ["validate", str(EXAMPLES / "packs" / "privacy.intent.yaml"), "--format", "json"],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True


def test_validate_command_reports_json_errors_to_stdout() -> None:
    result = runner.invoke(
        app,
        ["validate", str(EXAMPLES / "invalid_missing_goal.intent.yaml"), "--format", "json"],
    )
    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False


def test_inspect_command_returns_iir_json() -> None:
    result = runner.invoke(
        app,
        ["inspect", str(EXAMPLES / "customer_brief.intent.yaml"), "--format", "json"],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["normalized_goal"]
    assert "risk_signals" in payload


def test_inspect_command_supports_intent_pack() -> None:
    result = runner.invoke(
        app,
        ["inspect", str(EXAMPLES / "packs" / "privacy.intent.yaml"), "--format", "json"],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["kind"] == "IntentPack"
    assert payload["metadata"]["name"] == "privacy_pack"


def test_inspect_command_uses_schema_alias_in_json_output() -> None:
    result = runner.invoke(
        app,
        ["inspect", str(EXAMPLES / "report_json.intent.yaml"), "--format", "json"],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "schema" in payload["output_contract"]
    assert "json_schema" not in payload["output_contract"]


def test_compile_openai_structured_supports_out_file(tmp_path: Path) -> None:
    output_file = tmp_path / "structured.json"
    result = runner.invoke(
        app,
        [
            "compile",
            str(EXAMPLES / "report_json.intent.yaml"),
            "--target",
            "openai-structured",
            "--out",
            str(output_file),
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(output_file.read_text(encoding="utf-8"))
    assert payload["type"] == "json_schema"


def test_compile_agents_md_supports_out_file(tmp_path: Path) -> None:
    output_file = tmp_path / "AGENTS.md"
    result = runner.invoke(
        app,
        [
            "compile",
            str(EXAMPLES / "code_review.intent.yaml"),
            "--target",
            "agents-md",
            "--out",
            str(output_file),
        ],
    )
    assert result.exit_code == 0
    assert "## Project Goal" in output_file.read_text(encoding="utf-8")


def test_compile_claude_md_supports_out_file(tmp_path: Path) -> None:
    output_file = tmp_path / "CLAUDE.md"
    result = runner.invoke(
        app,
        [
            "compile",
            str(EXAMPLES / "code_review.intent.yaml"),
            "--target",
            "claude-md",
            "--out",
            str(output_file),
        ],
    )
    assert result.exit_code == 0
    assert "# CLAUDE.md" in output_file.read_text(encoding="utf-8")


def test_compile_cursor_rules_writes_bundle(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "compile",
            str(EXAMPLES / "code_review.intent.yaml"),
            "--target",
            "cursor-rules",
            "--out",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0
    assert (tmp_path / ".cursor" / "rules" / "intentspec.mdc").exists()


def test_compile_skill_writes_bundle(tmp_path: Path) -> None:
    output_dir = tmp_path / "skill"
    result = runner.invoke(
        app,
        [
            "compile",
            str(EXAMPLES / "code_review.intent.yaml"),
            "--target",
            "skill",
            "--out",
            str(output_dir),
        ],
    )
    assert result.exit_code == 0
    assert (output_dir / "SKILL.md").exists()


def test_compile_gemini_structured_supports_out_file(tmp_path: Path) -> None:
    output_file = tmp_path / "gemini.json"
    result = runner.invoke(
        app,
        [
            "compile",
            str(EXAMPLES / "report_json.intent.yaml"),
            "--target",
            "gemini-structured",
            "--out",
            str(output_file),
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(output_file.read_text(encoding="utf-8"))
    assert payload["generationConfig"]["responseMimeType"] == "application/json"


def test_test_command_supports_json_format() -> None:
    result = runner.invoke(
        app,
        [
            "test",
            str(EXAMPLES / "report_json.intent.yaml"),
            "--output",
            str(EXAMPLES / "report_json.output.json"),
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True


def test_test_command_reports_directory_output_as_clear_error() -> None:
    with runner.isolated_filesystem():
        intent_file = Path("report_json.intent.yaml")
        intent_file.write_text(
            (EXAMPLES / "report_json.intent.yaml").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        Path("output-dir").mkdir()
        result = runner.invoke(
            app,
            ["test", str(intent_file), "--output", "output-dir", "--format", "json"],
        )
        assert result.exit_code == 1
        payload = json.loads(result.stdout)
        assert "not a file" in payload["error"]["message"]


def test_test_command_rejects_semantically_invalid_spec(tmp_path: Path) -> None:
    output_file = tmp_path / "invalid.output.md"
    output_file.write_text("# Summary\n\nHello\n", encoding="utf-8")
    result = runner.invoke(
        app,
        [
            "test",
            str(EXAMPLES / "invalid_dangerous_permission.intent.yaml"),
            "--output",
            str(output_file),
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert "High-risk tool permissions" in payload["error"]["message"]


def test_schema_command_returns_json() -> None:
    result = runner.invoke(app, ["schema"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["title"] == "IntentSpecDocument"


def test_examples_command_lists_examples() -> None:
    result = runner.invoke(app, ["examples"])
    assert result.exit_code == 0
    assert "customer_brief.intent.yaml" in result.stdout
    assert "packs/privacy.intent.yaml" in result.stdout


def test_examples_command_can_copy_example(tmp_path: Path) -> None:
    output_file = tmp_path / "customer_brief.intent.yaml"
    result = runner.invoke(
        app,
        ["examples", "--copy", "customer_brief.intent.yaml", "--out", str(output_file)],
    )
    assert result.exit_code == 0
    assert output_file.exists()


def test_draft_command_writes_valid_yaml(tmp_path: Path) -> None:
    output_file = tmp_path / "draft.intent.yaml"
    result = runner.invoke(
        app,
        [
            "draft",
            "帮我做一份客户会议简报，别泄露隐私，必要时先问我",
            "--out",
            str(output_file),
        ],
    )
    assert result.exit_code == 0
    validate_result = runner.invoke(app, ["validate", str(output_file)])
    assert validate_result.exit_code == 0


def test_workflow_uses_json_output_default_for_json_tasks(tmp_path: Path) -> None:
    intent_file = tmp_path / "intent.yaml"
    output_file = tmp_path / "ai_output.json"
    intent_file.write_text(
        (EXAMPLES / "report_json.intent.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    output_file.write_text(
        (EXAMPLES / "report_json.output.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    result = runner.invoke(app, ["workflow", "--workdir", str(tmp_path)])
    assert result.exit_code == 0
    assert "task.openai-structured.json" in result.stdout
