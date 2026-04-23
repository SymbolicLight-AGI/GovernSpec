"""Typer CLI for IntentSpec v0.1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
import yaml
from intentspec_core import (
    SUPPORTED_IMPORT_TYPES,
    SUPPORTED_TARGETS,
    IntentSpecError,
    IntentSpecTestError,
    IntentSpecValidationError,
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
from intentspec_core.common.utils import dump_json, read_text, write_text
from intentspec_core.targets.compiler import CompiledArtifact
from intentspec_core.testing.tester import TestReport
from intentspec_core.validator import ValidationReport

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="IntentSpec local-first contract compiler for AI task systems.",
)

REPORT_FORMATS = {"text", "json"}
DEFAULT_INIT_FILENAME = "intent.yaml"
DEFAULT_INIT_CONTENT = """version: "0.1"
kind: "IntentSpec"

metadata:
  name: "my_intent"
  title: "Describe the task title"
  description: "Describe what this intent should produce."
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
  language: "zh-CN"
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


def _normalize_report_format(value: str) -> str:
    normalized = value.lower()
    if normalized not in REPORT_FORMATS:
        raise typer.BadParameter("Use one of: text, json.")
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
    except IntentSpecError as exc:
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
    except IntentSpecError as exc:
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
    except IntentSpecError as exc:
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
    except IntentSpecError as exc:
        _emit_error(exc, report_format)
        raise typer.Exit(code=1) from exc

    _emit_report(report, report_format)
    raise typer.Exit(code=0 if report.ok else 2)


@app.command()
def init(
    file: Path = typer.Option(
        Path(DEFAULT_INIT_FILENAME),
        "--file",
        help="Path to the new intent file.",
    ),
) -> None:
    _init_file(file)


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
    intent_file: Path = typer.Option(
        Path(DEFAULT_INIT_FILENAME),
        "--intent-file",
        help="IntentSpec file path.",
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
        help="Create the intent file before running the workflow.",
    ),
    skip_test: bool = typer.Option(
        False,
        "--skip-test",
        help="Skip the final intent test step.",
    ),
) -> None:
    try:
        resolved_workdir = workdir.resolve()
        resolved_intent_file = _resolve_workflow_path(resolved_workdir, intent_file)
        resolved_prompt_out = _resolve_workflow_path(resolved_workdir, prompt_out)
        resolved_structured_out = _resolve_workflow_path(resolved_workdir, structured_out)
        resolved_agents_out = _resolve_workflow_path(resolved_workdir, agents_out)
        resolved_mcp_plan_out = _resolve_workflow_path(resolved_workdir, mcp_plan_out)

        if init:
            _ensure_intent_file(resolved_intent_file)

        spec, report = _load_validated_spec(resolved_intent_file, emit_warnings=False)
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
            typer.echo("Skipped final intent test because --skip-test was provided.")
            raise typer.Exit(code=0)

        test_report = _run_test(resolved_intent_file, resolved_output_file)
        typer.echo(test_report.to_text())
        raise typer.Exit(code=0 if test_report.ok else 2)
    except typer.Exit:
        raise
    except IntentSpecError as exc:
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
        typer.echo(f"Wrote draft intent to {out}")
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
    except IntentSpecError as exc:
        _emit_error(exc, "text")
        raise typer.Exit(code=1) from exc

    rendered = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)
    if out is not None:
        if out.exists():
            typer.echo(f"Error: refusing to overwrite existing file: {out}", err=True)
            raise typer.Exit(code=1)
        write_text(out, rendered)
        typer.echo(f"Wrote imported intent to {out}")
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
            "Run `intent validate <file>` and fix the reported errors before testing "
            "output."
        ),
    )

    if not output.exists():
        raise IntentSpecTestError(
            f"Output file not found: {output}",
            suggestion="Create the output file or pass the correct --output path.",
            details={"path": str(output)},
        )
    if not output.is_file():
        raise IntentSpecTestError(
            f"Output path is not a file: {output}",
            suggestion="Pass a readable file path to --output, not a directory.",
            details={"path": str(output)},
        )
    try:
        output_text = read_text(output)
    except OSError as exc:
        raise IntentSpecTestError(
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
    raise IntentSpecValidationError(
        f"IntentSpec validation failed for {file}: {'; '.join(errors)}",
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


def _emit_error(exc: IntentSpecError, report_format: str) -> None:
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
            raise IntentSpecError(
                "Target produces a bundle and requires --out to point to a directory.",
                suggestion="Pass --out <directory> when compiling a bundle target.",
            )
        _write_bundle(out, artifact.files)
        typer.echo(f"Wrote bundle output to {out}")
        return

    if artifact.content is None:
        raise IntentSpecError("Compiled artifact is missing content.")

    if out is not None:
        write_text(out, artifact.content)
        typer.echo(f"Wrote compiled output to {out}")
        return
    typer.echo(artifact.content)


def _write_bundle(directory: Path, files: dict[str, str]) -> None:
    for relative_path, content in files.items():
        write_text(directory / relative_path, content)


def _init_file(file: Path) -> None:
    if file.exists():
        typer.echo(f"Refusing to overwrite existing file: {file}", err=True)
        raise typer.Exit(code=1)
    write_text(file, DEFAULT_INIT_CONTENT)
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


def _ensure_intent_file(file: Path) -> None:
    if file.exists():
        typer.echo(f"Using existing intent file: {file}")
        return
    _init_file(file)


def _render_iir_text(payload: dict[str, Any]) -> str:
    if payload.get("kind") == "IntentPack":
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
