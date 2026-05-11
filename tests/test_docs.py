from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_readme_intentpack_example_matches_pack_name() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert 'name: "privacy_pack"' in readme


def test_readme_python_sdk_documents_document_level_api() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for symbol in (
        "load_document",
        "resolve_document_imports",
        "inspect_document",
        "validate_document",
    ):
        assert symbol in readme


def test_readme_clarifies_offline_scope_and_mcp_surface() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "离线契约编译器" in readme
    assert "governspec-mcp" in readme


def test_release_checklist_examples_scope_is_precise() -> None:
    checklist = (ROOT / "docs" / "release-checklist.md").read_text(encoding="utf-8")
    assert "Validate every valid `.govern.yaml` example under `examples/`." in checklist
    expected_failure_line = (
        "Confirm expected-failure examples such as `invalid_*` still fail validation"
    )
    assert expected_failure_line in checklist


def test_release_checklist_includes_node_and_vscode_builds() -> None:
    checklist = (ROOT / "docs" / "release-checklist.md").read_text(encoding="utf-8")
    assert "packages/governspec-ts" in checklist
    assert "packages/governspec-vscode" in checklist
    assert "npm install && npm run build" in checklist


def test_benchmark_runner_reports_constraint_loss() -> None:
    result = subprocess.run(
        ["python", "benchmark/run_benchmark.py", "--format", "json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert "constraint_loss_count" in payload
    assert payload["constraint_loss_count"] >= 0
    assert all("constraint_loss" in item for item in payload["results"])


def test_release_notes_exist_for_v020() -> None:
    release_notes = (ROOT / "docs" / "release-notes-v0.1.0.md").read_text(
        encoding="utf-8"
    )
    assert "GovernSpec v0.1.0 Release Notes" in release_notes
    assert "Recommended git tag: `v0.1.0`" in release_notes
    assert "`pytest`: `210 passed`" in release_notes
    assert "packages/governspec-vscode" in release_notes


def test_github_release_copy_mentions_main_v020_capabilities() -> None:
    github_release = (ROOT / "docs" / "github-release-v0.1.0.md").read_text(
        encoding="utf-8"
    )
    for snippet in (
        "output.schema",
        "GovernPack",
        "governspec inspect",
        "openai-structured",
        "gemini-structured",
        "agents-md",
        "claude-md",
        "constraint_loss",
        "`v0.1.0`",
    ):
        assert snippet in github_release


def test_ci_workflow_builds_node_packages() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    for snippet in (
        "node-build:",
        "actions/setup-node@v4",
        "packages/governspec-ts",
        "packages/governspec-vscode",
        "npm run build",
    ):
        assert snippet in workflow


def test_manifest_excludes_node_modules_and_frontend_dist() -> None:
    manifest = (ROOT / "MANIFEST.in").read_text(encoding="utf-8")
    for snippet in (
        "prune packages/governspec-ts/node_modules",
        "prune packages/governspec-vscode/node_modules",
        "prune packages/governspec-ts/dist",
        "prune packages/governspec-vscode/dist",
    ):
        assert snippet in manifest
