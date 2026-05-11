"""Tests for the enhanced heuristic draft generator."""

from __future__ import annotations

from pathlib import Path

import yaml
from governspec.cli import app
from governspec_core.draft import heuristic_draft_payload
from governspec_core.imports.resolver import resolve_imports
from governspec_core.spec.parser import load_spec
from governspec_core.validator import validate_spec
from typer.testing import CliRunner

runner = CliRunner()


# ---------------------------------------------------------------------------
# Language detection
# ---------------------------------------------------------------------------


def test_detect_language_chinese() -> None:
    result = heuristic_draft_payload("帮我做一份客户会议简报")
    assert result["output"].get("language") == "zh-CN"


def test_detect_language_english() -> None:
    result = heuristic_draft_payload("Review this repository")
    assert result["output"].get("language") == "en"


def test_detect_language_mixed_mostly_chinese() -> None:
    result = heuristic_draft_payload("帮我做一份关于 Python 项目的审查报告")
    assert result["output"].get("language") == "zh-CN"


def test_detect_language_mixed_mostly_english() -> None:
    result = heuristic_draft_payload(
        "Generate a market analysis report for the APAC region"
    )
    assert result["output"].get("language") == "en"


# ---------------------------------------------------------------------------
# Profile detection
# ---------------------------------------------------------------------------


def test_profile_review_english() -> None:
    result = heuristic_draft_payload("Review this repository without modifying code")
    assert "review" in result["task"]["goal"].lower()


def test_profile_review_chinese() -> None:
    result = heuristic_draft_payload("审查这个代码仓库")
    assert "审查" in result["task"]["goal"] or "代码" in result["task"]["goal"]


def test_profile_brief() -> None:
    result = heuristic_draft_payload("Write a customer meeting brief")
    assert "brief" in result["task"]["goal"].lower()


def test_profile_brief_chinese() -> None:
    result = heuristic_draft_payload("帮我做一份客户简报")
    assert "简报" in result["task"]["goal"] or "客户" in result["task"]["goal"]


def test_profile_deploy() -> None:
    result = heuristic_draft_payload("Deploy the app to staging environment")
    assert "deploy" in result["task"]["goal"].lower()


def test_profile_test_plan() -> None:
    result = heuristic_draft_payload("Generate a test plan for the login module")
    assert "test" in result["task"]["goal"].lower()


def test_profile_translate() -> None:
    result = heuristic_draft_payload("Translate this document to Japanese")
    assert "translate" in result["task"]["goal"].lower()


def test_profile_summarize() -> None:
    result = heuristic_draft_payload("Summarize the meeting notes")
    assert "summar" in result["task"]["goal"].lower()


def test_profile_summarize_chinese() -> None:
    result = heuristic_draft_payload("帮我总结一下这篇文章")
    assert "总结" in result["task"]["goal"] or "文章" in result["task"]["goal"]


def test_profile_default_is_analysis() -> None:
    result = heuristic_draft_payload("Do something interesting with data")
    assert result["kind"] == "GovernSpec"
    assert result["task"]["goal"]


# ---------------------------------------------------------------------------
# Priority detection
# ---------------------------------------------------------------------------


def test_priority_high_english() -> None:
    result = heuristic_draft_payload("Urgent: review the security logs immediately")
    assert result["task"]["priority"] == "high"


def test_priority_high_chinese() -> None:
    result = heuristic_draft_payload("紧急：帮我分析一下这个 bug")
    assert result["task"]["priority"] == "high"


def test_priority_low_english() -> None:
    result = heuristic_draft_payload("When you have time, review the docs")
    assert result["task"]["priority"] == "low"


def test_priority_low_chinese() -> None:
    result = heuristic_draft_payload("不着急，有空帮我看看代码")
    assert result["task"]["priority"] == "low"


def test_priority_default_medium() -> None:
    result = heuristic_draft_payload("Generate a report on sales data")
    assert result["task"]["priority"] == "medium"


# ---------------------------------------------------------------------------
# Output format detection
# ---------------------------------------------------------------------------


def test_format_json_english() -> None:
    result = heuristic_draft_payload("Generate a JSON report with verdict and risks")
    assert result["output"]["format"] == "json"
    assert "schema" in result["output"]


def test_format_json_chinese() -> None:
    result = heuristic_draft_payload("请给我结构化输出，包含分析结果")
    assert result["output"]["format"] == "json"


def test_format_json_structured_output() -> None:
    result = heuristic_draft_payload("Produce a structured output with schema")
    assert result["output"]["format"] == "json"


def test_format_json_generates_schema_test() -> None:
    result = heuristic_draft_payload("Generate JSON output")
    assert any(t["name"] == "Must match JSON schema" for t in result["tests"])


def test_format_default_markdown() -> None:
    result = heuristic_draft_payload("Write a report about the project")
    assert result["output"]["format"] == "markdown"


# ---------------------------------------------------------------------------
# Permission inference
# ---------------------------------------------------------------------------


def test_permissions_default_safe() -> None:
    result = heuristic_draft_payload("Generate a simple report")
    p = result["permissions"]
    assert p["web"] is False
    assert p["network"] is False
    assert p["filesystem"]["read"] is True
    assert p["filesystem"]["write"] is False


def test_permissions_web_allowed_english() -> None:
    result = heuristic_draft_payload("Browse the web and fetch latest news")
    assert result["permissions"]["web"] is True


def test_permissions_web_allowed_chinese() -> None:
    result = heuristic_draft_payload("联网查询最新的市场数据")
    assert result["permissions"]["web"] is True
    assert result["permissions"]["network"] is True


def test_permissions_write_allowed() -> None:
    result = heuristic_draft_payload("Write files to the output directory")
    assert result["permissions"]["filesystem"]["write"] is True


def test_permissions_write_allowed_chinese() -> None:
    result = heuristic_draft_payload("帮我生成文件到输出目录")
    assert result["permissions"]["tools"]["create_file"] is True


def test_permissions_no_modify_english() -> None:
    result = heuristic_draft_payload("Do not modify any existing files")
    assert result["permissions"]["filesystem"]["write"] is False


def test_permissions_no_modify_chinese() -> None:
    result = heuristic_draft_payload("不要修改任何文件")
    assert result["permissions"]["filesystem"]["write"] is False


def test_permissions_send_email_allowed() -> None:
    result = heuristic_draft_payload("Send an email summary to the team")
    assert result["permissions"]["tools"]["send_email"] is True


def test_permissions_purchase_allowed() -> None:
    result = heuristic_draft_payload("Purchase the listed items from the supplier")
    assert result["permissions"]["tools"]["purchase"] is True


def test_permissions_calendar_allowed() -> None:
    result = heuristic_draft_payload("Check my calendar for conflicts")
    assert result["permissions"]["tools"]["read_calendar"] is True


# ---------------------------------------------------------------------------
# Constraint inference
# ---------------------------------------------------------------------------


def test_constraints_always_includes_no_fabricate() -> None:
    result = heuristic_draft_payload("Do something")
    assert "Do not fabricate facts." in result["constraints"]


def test_constraints_privacy() -> None:
    result = heuristic_draft_payload("Analyze data but protect privacy")
    assert any("private" in c.lower() or "personal" in c.lower()
               for c in result["constraints"])


def test_constraints_privacy_chinese() -> None:
    result = heuristic_draft_payload("分析数据，注意保护隐私")
    assert any("private" in c.lower() or "personal" in c.lower()
               for c in result["constraints"])


def test_constraints_no_modify() -> None:
    result = heuristic_draft_payload("Review code, do not modify anything")
    assert any("modify" in c.lower() for c in result["constraints"])


def test_constraints_no_delete() -> None:
    result = heuristic_draft_payload("不要删除任何文件")
    assert any("delete" in c.lower() for c in result["constraints"])


def test_constraints_confidential() -> None:
    result = heuristic_draft_payload("Handle this confidential document")
    assert any("confidential" in c.lower() for c in result["constraints"])


# ---------------------------------------------------------------------------
# Human gate inference
# ---------------------------------------------------------------------------


def test_gates_privacy() -> None:
    result = heuristic_draft_payload("Analyze data with privacy considerations")
    gates = result["human_gates"]
    assert any("privacy" in g["when"].lower() for g in gates)


def test_gates_confirm_chinese() -> None:
    result = heuristic_draft_payload("帮我分析数据，重要操作先问我")
    gates = result["human_gates"]
    assert any(g["action"] == "ask_confirmation" for g in gates)


def test_gates_web_access() -> None:
    result = heuristic_draft_payload("Browse the internet for information")
    gates = result["human_gates"]
    assert any("network" in g["when"].lower() or "external" in g["when"].lower()
               for g in gates)


def test_gates_delete_operation() -> None:
    result = heuristic_draft_payload("Clean up old files by deleting them")
    gates = result["human_gates"]
    assert any("destructive" in g["when"].lower() for g in gates)


def test_gates_purchase() -> None:
    result = heuristic_draft_payload("Purchase office supplies from the vendor")
    gates = result["human_gates"]
    assert any("financial" in g["when"].lower() for g in gates)


def test_gates_high_risk_tool_auto_gate() -> None:
    result = heuristic_draft_payload("Send an email to the client with the report")
    gates = result["human_gates"]
    assert any("send_email" in g["when"] for g in gates)


def test_gates_no_duplicates() -> None:
    result = heuristic_draft_payload(
        "隐私很重要，保护隐私，关于隐私的分析"
    )
    when_texts = [g["when"] for g in result["human_gates"]]
    assert len(when_texts) == len(set(when_texts))


# ---------------------------------------------------------------------------
# Section extraction
# ---------------------------------------------------------------------------


def test_sections_extracted_chinese() -> None:
    result = heuristic_draft_payload("写一份报告，包含结论、风险和建议")
    sections = result["output"]["sections"]
    assert "结论" in sections
    assert "风险" in sections
    assert "建议" in sections


def test_sections_extracted_english() -> None:
    result = heuristic_draft_payload(
        "Generate a report including summary, risks, and recommendations"
    )
    sections = result["output"]["sections"]
    assert "summary" in [s.lower() for s in sections]
    assert "risks" in [s.lower() for s in sections]
    assert "recommendations" in [s.lower() for s in sections]


def test_sections_with_colon() -> None:
    result = heuristic_draft_payload("报告需要包含：概述、分析、结论")
    sections = result["output"]["sections"]
    assert len(sections) == 3
    assert "概述" in sections


def test_sections_fallback_to_profile() -> None:
    result = heuristic_draft_payload("Review the code")
    sections = result["output"]["sections"]
    assert len(sections) >= 2


# ---------------------------------------------------------------------------
# Goal extraction
# ---------------------------------------------------------------------------


def test_goal_extracted_from_prompt() -> None:
    result = heuristic_draft_payload("Analyze the quarterly sales data for trends")
    assert "quarterly sales" in result["task"]["goal"].lower()


def test_goal_extracted_chinese() -> None:
    result = heuristic_draft_payload("帮我做一份客户会议简报，别泄露隐私")
    assert "客户会议简报" in result["task"]["goal"]


def test_goal_not_empty() -> None:
    result = heuristic_draft_payload("x")
    assert result["task"]["goal"]


# ---------------------------------------------------------------------------
# Title extraction
# ---------------------------------------------------------------------------


def test_title_from_prompt() -> None:
    result = heuristic_draft_payload("Generate a security audit report")
    assert result["metadata"]["title"]
    assert len(result["metadata"]["title"]) <= 80


def test_title_truncated_for_long_prompt() -> None:
    long_prompt = "A" * 200
    result = heuristic_draft_payload(long_prompt)
    assert len(result["metadata"]["title"]) <= 80


# ---------------------------------------------------------------------------
# End-to-end: draft → validate
# ---------------------------------------------------------------------------


def _draft_and_validate(prompt: str, tmp_path: Path) -> None:
    payload = heuristic_draft_payload(prompt)
    draft_path = tmp_path / "draft.govern.yaml"
    draft_path.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    spec = resolve_imports(load_spec(draft_path))
    report = validate_spec(spec)
    assert report.ok, f"Validation failed for '{prompt}': {report.errors}"


def test_e2e_chinese_brief(tmp_path: Path) -> None:
    _draft_and_validate("帮我做一份客户会议简报，别泄露隐私，必要时先问我", tmp_path)


def test_e2e_english_review(tmp_path: Path) -> None:
    _draft_and_validate("Review this repository without modifying code", tmp_path)


def test_e2e_json_output(tmp_path: Path) -> None:
    _draft_and_validate("Generate a JSON report with verdict and risks", tmp_path)


def test_e2e_web_access(tmp_path: Path) -> None:
    _draft_and_validate("联网帮我搜集最新的市场信息，必要时先问我", tmp_path)


def test_e2e_deploy(tmp_path: Path) -> None:
    _draft_and_validate("Deploy the application to staging", tmp_path)


def test_e2e_translate(tmp_path: Path) -> None:
    _draft_and_validate("Translate this README to Japanese", tmp_path)


def test_e2e_summarize(tmp_path: Path) -> None:
    _draft_and_validate("帮我总结一下这篇论文的要点", tmp_path)


def test_e2e_high_priority(tmp_path: Path) -> None:
    _draft_and_validate("Urgent: fix the production bug", tmp_path)


def test_e2e_with_sections(tmp_path: Path) -> None:
    _draft_and_validate("写一份报告，包含结论、风险和建议", tmp_path)


def test_e2e_send_email(tmp_path: Path) -> None:
    _draft_and_validate("Send an email summary to the team", tmp_path)


def test_e2e_purchase(tmp_path: Path) -> None:
    _draft_and_validate("Purchase office supplies from the vendor", tmp_path)


# ---------------------------------------------------------------------------
# CLI: governspec draft
# ---------------------------------------------------------------------------


def test_cli_draft_backward_compat(tmp_path: Path) -> None:
    output_file = tmp_path / "draft.govern.yaml"
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


def test_cli_draft_english_review(tmp_path: Path) -> None:
    output_file = tmp_path / "draft.govern.yaml"
    result = runner.invoke(
        app,
        ["draft", "Review this repo without modifying code", "--out", str(output_file)],
    )
    assert result.exit_code == 0
    data = yaml.safe_load(output_file.read_text(encoding="utf-8"))
    assert data["output"]["language"] == "en"


def test_cli_draft_json_format(tmp_path: Path) -> None:
    result = runner.invoke(app, ["draft", "Generate a JSON structured output"])
    assert result.exit_code == 0
    data = yaml.safe_load(result.stdout)
    assert data["output"]["format"] == "json"


def test_cli_draft_high_priority() -> None:
    result = runner.invoke(app, ["draft", "Urgent security review needed"])
    assert result.exit_code == 0
    data = yaml.safe_load(result.stdout)
    assert data["task"]["priority"] == "high"


def test_cli_draft_with_sections() -> None:
    result = runner.invoke(
        app,
        ["draft", "写一份报告，包含结论、风险和建议"],
    )
    assert result.exit_code == 0
    data = yaml.safe_load(result.stdout)
    assert "结论" in data["output"]["sections"]
    assert "风险" in data["output"]["sections"]
    assert "建议" in data["output"]["sections"]
