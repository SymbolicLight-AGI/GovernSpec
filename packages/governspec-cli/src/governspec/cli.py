"""Typer CLI for GovernSpec v0.1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
import yaml
from governspec_core import (
    SUPPORTED_IMPORT_TYPES,
    SUPPORTED_TARGETS,
    GovernSpecError,
    GovernSpecTestError,
    GovernSpecValidationError,
    compile_target,
    copy_example,
    generate_json_schema,
    heuristic_draft_payload,
    import_from_artifact,
    inspect_document,
    list_examples,
    load_document,
    load_spec,
    resolve_document_imports,
    resolve_imports,
    run_doctor,
    test_output,
    validate_document,
    validate_spec,
)
from governspec_core.common.utils import dump_json, read_text, write_text
from governspec_core.targets.compiler import CompiledArtifact
from governspec_core.testing.tester import TestReport
from governspec_core.validator import ValidationReport

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="GovernSpec local-first contract compiler for AI task systems.",
)

REPORT_FORMATS = {"text", "json"}
INIT_LOCALES = {"en", "zh-cn"}
DEFAULT_INIT_FILENAME = "govern.yaml"
DEFAULT_INIT_LOCALE = "en"
EN_INIT_CONTENT = """version: "0.1"
kind: "GovernSpec"

metadata:
  name: "my_govern_contract"
  title: "Describe the task title"
  description: "Describe what this contract should produce."
  owner: "team-name"

task:
  goal: "Describe the main goal for the system."
  audience:
    - "Primary audience"
  priority: "medium"

context:
  domain: "General"
  facts: []
  assumptions: []
  glossary: {}

inputs: []

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

constraints:
  - "Do not fabricate facts."

evidence:
  require_sources: false
  mark_uncertainty: true
  distinguish:
    - "fact"
    - "inference"

output:
  format: "markdown"
  language: "en"
  max_words: 500
  sections:
    - "Summary"

quality:
  tone:
    - "clear"
  must_include: []
  must_avoid: []

human_gates: []

tests:
  - name: "Must include all sections"
    assert:
      - type: "required_sections"
"""
ZH_CN_INIT_CONTENT = """version: "0.1"
kind: "GovernSpec"

metadata:
  name: "my_govern_contract"
  title: "请填写任务标题"
  description: "请说明这个任务希望产出什么结果。"
  owner: "团队或负责人名称"

task:
  goal: "请描述智能体本次要完成的主要目标。"
  audience:
    - "主要读者或使用者"
  priority: "medium"

context:
  domain: "通用"
  facts: []
  assumptions: []
  glossary: {}

inputs: []

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

constraints:
  - "不得编造事实、数据、来源或用户未提供的信息。"
  - "信息不足时，应明确说明假设和不确定性。"
  - "涉及高风险操作、隐私数据或不可逆修改时，应先请求人工确认。"

evidence:
  require_sources: false
  mark_uncertainty: true
  distinguish:
    - "事实"
    - "推断"

output:
  format: "markdown"
  language: "zh-CN"
  max_words: 500
  sections:
    - "摘要"

quality:
  tone:
    - "清晰"
  must_include: []
  must_avoid: []

human_gates: []

tests:
  - name: "必须包含所有指定章节"
    assert:
      - type: "required_sections"
"""
INIT_CONTENT_BY_LOCALE = {
    "en": EN_INIT_CONTENT,
    "zh-cn": ZH_CN_INIT_CONTENT,
}


def _normalize_report_format(value: str) -> str:
    normalized = value.lower()
    if normalized not in REPORT_FORMATS:
        raise typer.BadParameter("Use one of: text, json.")
    return normalized


def _normalize_init_locale(value: str) -> str:
    normalized = value.lower()
    if normalized in {"zh", "zh_cn"}:
        normalized = "zh-cn"
    if normalized not in INIT_LOCALES:
        raise typer.BadParameter("Use one of: en, zh-CN.")
    return normalized


@app.command()
def validate(
    file: Path,
    report_format: str = typer.Option(
        "text",
        "--format",
        callback=_normalize_report_format,
        help="Output format: text or json.",
    ),
) -> None:
    try:
        report = _validate_document(file)
    except GovernSpecError as exc:
        _emit_error(exc, report_format)
        raise typer.Exit(code=1) from exc

    _emit_report(report, report_format)
    raise typer.Exit(code=0 if report.ok else 1)


@app.command()
def inspect(
    file: Path,
    report_format: str = typer.Option(
        "text",
        "--format",
        callback=_normalize_report_format,
        help="Output format: text or json.",
    ),
) -> None:
    try:
        document, _ = _load_validated_document(file, emit_warnings=False)
        payload = inspect_document(document)
    except GovernSpecError as exc:
        _emit_error(exc, report_format)
        raise typer.Exit(code=1) from exc

    if report_format == "json":
        typer.echo(dump_json(payload))
    else:
        typer.echo(_render_iir_text(payload))


@app.command()
def compile(
    file: Path,
    target: str = typer.Option(
        ...,
        "--target",
        help=f"One of: {', '.join(sorted(SUPPORTED_TARGETS))}",
    ),
    out: Path | None = typer.Option(None, "--out", help="Optional output file or directory."),
) -> None:
    try:
        spec, _ = _load_validated_spec(file, emit_warnings=True)
        artifact = compile_target(spec, target)
    except typer.Exit:
        raise
    except GovernSpecError as exc:
        _emit_error(exc, "text")
        raise typer.Exit(code=1) from exc

    _emit_compiled_artifact(artifact, out)


@app.command("test")
def test_command(
    file: Path,
    output: Path = typer.Option(..., "--output", help="Output text or JSON file to test."),
    report_format: str = typer.Option(
        "text",
        "--format",
        callback=_normalize_report_format,
        help="Output format: text or json.",
    ),
) -> None:
    try:
        report = _run_test(file, output)
    except GovernSpecError as exc:
        _emit_error(exc, report_format)
        raise typer.Exit(code=1) from exc

    _emit_report(report, report_format)
    raise typer.Exit(code=0 if report.ok else 2)


@app.command()
def init(
    file: Path = typer.Option(
        Path(DEFAULT_INIT_FILENAME),
        "--file",
        help="Path to the new GovernSpec file.",
    ),
    locale: str = typer.Option(
        DEFAULT_INIT_LOCALE,
        "--locale",
        callback=_normalize_init_locale,
        help="Template language: en or zh-CN.",
    ),
) -> None:
    _init_file(file, locale=locale)


@app.command()
def schema(
    out: Path | None = typer.Option(None, "--out", help="Optional output file path."),
) -> None:
    rendered = dump_json(generate_json_schema())
    if out is not None:
        write_text(out, rendered)
        typer.echo(f"Wrote schema to {out}")
        return
    typer.echo(rendered)


@app.command()
def doctor(
    report_format: str = typer.Option(
        "text",
        "--format",
        callback=_normalize_report_format,
        help="Output format: text or json.",
    ),
) -> None:
    report = run_doctor(Path.cwd())
    _emit_report(report, report_format)
    raise typer.Exit(code=0 if report.ok else 1)


@app.command()
def examples(
    copy: str | None = typer.Option(None, "--copy", help="Copy a packaged example by filename."),
    out: Path | None = typer.Option(None, "--out", help="Destination path for --copy."),
) -> None:
    if copy is None:
        typer.echo("Available examples:")
        for example in list_examples():
            typer.echo(f"- {example.name}")
        return

    if out is None:
        typer.echo("Error: --out is required when using --copy.", err=True)
        raise typer.Exit(code=1)
    if out.exists():
        typer.echo(f"Error: refusing to overwrite existing path: {out}", err=True)
        raise typer.Exit(code=1)

    try:
        destination = copy_example(copy, out)
    except FileNotFoundError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Copied example '{copy}' to {destination}")


@app.command()
def workflow(
    workdir: Path = typer.Option(
        Path("."),
        "--workdir",
        help="Working directory for relative paths.",
    ),
    govern_file: Path = typer.Option(
        Path(DEFAULT_INIT_FILENAME),
        "--govern-file",
        help="GovernSpec file path.",
    ),
    prompt_out: Path = typer.Option(
        Path("task.prompt.md"),
        "--prompt-out",
        help="Prompt output path.",
    ),
    structured_out: Path = typer.Option(
        Path("task.openai-structured.json"),
        "--openai-structured-out",
        help="Structured output payload path.",
    ),
    agents_out: Path = typer.Option(
        Path("AGENTS.md"),
        "--agents-out",
        help="AGENTS.md output path.",
    ),
    mcp_plan_out: Path = typer.Option(
        Path("task.mcp-plan.json"),
        "--mcp-plan-out",
        help="MCP plan output path.",
    ),
    output_file: Path = typer.Option(
        None,
        "--output-file",
        help="AI output file path. Defaults to ai_output.md or ai_output.json by format.",
    ),
    init: bool = typer.Option(
        False,
        "--init",
        help="Create the GovernSpec file before running the workflow.",
    ),
    skip_test: bool = typer.Option(
        False,
        "--skip-test",
        help="Skip the final governspec test step.",
    ),
) -> None:
    try:
        resolved_workdir = workdir.resolve()
        resolved_govern_file = _resolve_workflow_path(resolved_workdir, govern_file)
        resolved_prompt_out = _resolve_workflow_path(resolved_workdir, prompt_out)
        resolved_structured_out = _resolve_workflow_path(resolved_workdir, structured_out)
        resolved_agents_out = _resolve_workflow_path(resolved_workdir, agents_out)
        resolved_mcp_plan_out = _resolve_workflow_path(resolved_workdir, mcp_plan_out)

        if init:
            _ensure_govern_file(resolved_govern_file)

        spec, report = _load_validated_spec(resolved_govern_file, emit_warnings=False)
        resolved_output_file = _resolve_workflow_output_file(
            resolved_workdir,
            output_file,
            spec.output.format,
        )
        typer.echo(report.to_text())
        _emit_compiled_artifact(compile_target(spec, "prompt"), resolved_prompt_out)
        if spec.output.format == "json":
            _emit_compiled_artifact(
                compile_target(spec, "openai-structured"),
                resolved_structured_out,
            )
        _emit_compiled_artifact(compile_target(spec, "agents-md"), resolved_agents_out)
        _emit_compiled_artifact(compile_target(spec, "mcp-plan"), resolved_mcp_plan_out)

        if skip_test:
            typer.echo("Skipped final governspec test because --skip-test was provided.")
            raise typer.Exit(code=0)

        test_report = _run_test(resolved_govern_file, resolved_output_file)
        typer.echo(test_report.to_text())
        raise typer.Exit(code=0 if test_report.ok else 2)
    except typer.Exit:
        raise
    except GovernSpecError as exc:
        _emit_error(exc, "text")
        raise typer.Exit(code=1) from exc


@app.command()
def draft(
    request: str,
    out: Path | None = typer.Option(None, "--out", help="Optional output file path."),
    backend: str = typer.Option(
        "heuristic",
        "--backend",
        help="Draft backend. Only heuristic is supported.",
    ),
) -> None:
    if backend != "heuristic":
        typer.echo("Error: only the heuristic draft backend is supported in v0.1.", err=True)
        raise typer.Exit(code=1)
    payload = heuristic_draft_payload(request)
    rendered = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)
    if out is not None:
        if out.exists():
            typer.echo(f"Error: refusing to overwrite existing file: {out}", err=True)
            raise typer.Exit(code=1)
        write_text(out, rendered)
        typer.echo(f"Wrote draft GovernSpec contract to {out}")
        return
    typer.echo(rendered)


def _validate_import_type(value: str | None) -> str | None:
    if value is None:
        return None
    if value not in SUPPORTED_IMPORT_TYPES:
        raise typer.BadParameter(
            f"Use one of: {', '.join(sorted(SUPPORTED_IMPORT_TYPES))}."
        )
    return value


@app.command("import")
def import_command(
    file: Path,
    source_type: str | None = typer.Option(
        None,
        "--type",
        callback=_validate_import_type,
        help=f"Source artifact type. One of: {', '.join(sorted(SUPPORTED_IMPORT_TYPES))}. "
        "Inferred from file when omitted.",
    ),
    out: Path | None = typer.Option(None, "--out", help="Optional output YAML file path."),
) -> None:
    try:
        payload = import_from_artifact(file, source_type)
    except GovernSpecError as exc:
        _emit_error(exc, "text")
        raise typer.Exit(code=1) from exc

    rendered = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)
    if out is not None:
        if out.exists():
            typer.echo(f"Error: refusing to overwrite existing file: {out}", err=True)
            raise typer.Exit(code=1)
        write_text(out, rendered)
        typer.echo(f"Wrote imported GovernSpec contract to {out}")
        return
    typer.echo(rendered)


def main() -> None:
    app()


def _validate_document(file: Path) -> ValidationReport:
    document = resolve_document_imports(load_document(file))
    return validate_document(document)


def _load_validated_spec(file: Path, *, emit_warnings: bool) -> tuple[Any, ValidationReport]:
    spec = resolve_imports(load_spec(file))
    report = validate_spec(spec)
    if not report.ok:
        typer.echo(report.to_text(), err=True)
        raise typer.Exit(code=1)
    if emit_warnings and report.warnings:
        typer.echo("Warnings:", err=True)
        for warning in report.warnings:
            typer.echo(f"- {warning}", err=True)
    return spec, report


def _load_validated_document(
    file: Path, *, emit_warnings: bool
) -> tuple[Any, ValidationReport]:
    document = resolve_document_imports(load_document(file))
    report = validate_document(document)
    if not report.ok:
        typer.echo(report.to_text(), err=True)
        raise typer.Exit(code=1)
    if emit_warnings and report.warnings:
        typer.echo("Warnings:", err=True)
        for warning in report.warnings:
            typer.echo(f"- {warning}", err=True)
    return document, report


def _run_test(file: Path, output: Path) -> TestReport:
    spec = resolve_imports(load_spec(file))
    validation_report = validate_spec(spec)
    _ensure_validation_report_ok(
        validation_report,
        file,
        suggestion=(
            "Run `governspec validate <file>` and fix the reported errors before testing "
            "output."
        ),
    )

    if not output.exists():
        raise GovernSpecTestError(
            f"Output file not found: {output}",
            suggestion="Create the output file or pass the correct --output path.",
            details={"path": str(output)},
        )
    if not output.is_file():
        raise GovernSpecTestError(
            f"Output path is not a file: {output}",
            suggestion="Pass a readable file path to --output, not a directory.",
            details={"path": str(output)},
        )
    try:
        output_text = read_text(output)
    except OSError as exc:
        raise GovernSpecTestError(
            f"Unable to read output file: {output}",
            suggestion="Verify the output path is readable and points to a text or JSON file.",
            details={"path": str(output)},
        ) from exc

    return test_output(spec, output_text)


def _ensure_validation_report_ok(
    report: ValidationReport,
    file: Path,
    *,
    suggestion: str,
) -> None:
    if report.ok:
        return

    errors = report.errors or ["Unknown validation error."]
    raise GovernSpecValidationError(
        f"GovernSpec validation failed for {file}: {'; '.join(errors)}",
        suggestion=suggestion,
        details={
            "path": str(file),
            "errors": report.errors,
            "warnings": report.warnings,
        },
    )


def _emit_report(report: Any, report_format: str) -> None:
    if report_format == "json":
        typer.echo(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        return
    typer.echo(report.to_text())


def _emit_error(exc: GovernSpecError, report_format: str) -> None:
    if report_format == "json":
        typer.echo(
            json.dumps(
                {"ok": False, "error": exc.to_dict()},
                ensure_ascii=False,
                indent=2,
            )
        )
        return
    typer.echo(f"Error: {exc}", err=True)
    if exc.suggestion:
        typer.echo(f"Suggested fix: {exc.suggestion}", err=True)


def _emit_compiled_artifact(artifact: CompiledArtifact, out: Path | None) -> None:
    if artifact.kind == "bundle":
        if out is None:
            raise GovernSpecError(
                "Target produces a bundle and requires --out to point to a directory.",
                suggestion="Pass --out <directory> when compiling a bundle target.",
            )
        _write_bundle(out, artifact.files)
        typer.echo(f"Wrote bundle output to {out}")
        return

    if artifact.content is None:
        raise GovernSpecError("Compiled artifact is missing content.")

    if out is not None:
        write_text(out, artifact.content)
        typer.echo(f"Wrote compiled output to {out}")
        return
    typer.echo(artifact.content)


def _write_bundle(directory: Path, files: dict[str, str]) -> None:
    for relative_path, content in files.items():
        write_text(directory / relative_path, content)


def _init_file(file: Path, *, locale: str = DEFAULT_INIT_LOCALE) -> None:
    if file.exists():
        typer.echo(f"Refusing to overwrite existing file: {file}", err=True)
        raise typer.Exit(code=1)
    write_text(file, INIT_CONTENT_BY_LOCALE[locale])
    typer.echo(f"Created {file}")


def _resolve_workflow_path(workdir: Path, path: Path) -> Path:
    if path.is_absolute():
        return path
    return workdir / path


def _resolve_workflow_output_file(
    workdir: Path,
    output_file: Path | None,
    output_format: str,
) -> Path:
    if output_file is None:
        default_name = "ai_output.json" if output_format == "json" else "ai_output.md"
        return workdir / default_name
    return _resolve_workflow_path(workdir, output_file)


def _ensure_govern_file(file: Path) -> None:
    if file.exists():
        typer.echo(f"Using existing GovernSpec file: {file}")
        return
    _init_file(file)


def _render_iir_text(payload: dict[str, Any]) -> str:
    if payload.get("kind") == "GovernPack":
        lines = [
            f"Source path: {payload['source_path']}",
            f"Pack: {payload['metadata']['name']}",
            "Constraints:",
            *[f"- {item}" for item in payload["merged_constraints"]],
        ]
        return "\n".join(lines)

    lines = [
        f"Source path: {payload['source_path']}",
        f"Goal: {payload['normalized_goal']}",
        "Risk signals:",
        *[f"- {item}" for item in payload["risk_signals"]],
        "Constraints:",
        *[f"- {item}" for item in payload["merged_constraints"]],
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
