from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_integrations_doc_mentions_all_supported_integrations() -> None:
    content = (ROOT / "docs" / "integrations.md").read_text(encoding="utf-8")
    for snippet in (
        "claude-md",
        "cursor-rules",
        "gemini-structured",
        "antigravity-rules",
        "Available IntentSpec artifacts",
        "generic bundle target",
        "intent://compiled/<target>/<path>",
        "Copilot-specific target",
    ):
        assert snippet in content


def test_readme_mentions_new_compile_targets_and_integrations_doc() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for snippet in (
        "gemini-structured",
        "claude-md",
        "cursor-rules",
        "antigravity-rules",
        "IntentSpec 产物",
        "docs/integrations.md",
    ):
        assert snippet in readme


def test_vscode_extension_manifest_registers_expected_commands() -> None:
    package_json = json.loads(
        (ROOT / "packages" / "intentspec-vscode" / "package.json").read_text(encoding="utf-8")
    )
    commands = {
        command["command"]
        for command in package_json["contributes"]["commands"]
    }
    assert {
        "intentspec.validateCurrentFile",
        "intentspec.inspectCurrentFile",
        "intentspec.compileCurrentFile",
        "intentspec.testOutput",
        "intentspec.showMcpSetupSnippet",
    }.issubset(commands)


def test_vscode_extension_source_mentions_supported_compile_targets() -> None:
    source = (
        ROOT / "packages" / "intentspec-vscode" / "src" / "extension.ts"
    ).read_text(encoding="utf-8")
    for snippet in (
        '"agents-md"',
        '"claude-md"',
        '"cursor-rules"',
        '"openai-structured"',
        '"gemini-structured"',
        '"mcp-plan"',
        '"antigravity-rules"',
    ):
        assert snippet in source


def test_vscode_extension_accepts_json_failure_exit_codes_for_validate_and_test() -> None:
    source = (
        ROOT / "packages" / "intentspec-vscode" / "src" / "extension.ts"
    ).read_text(encoding="utf-8")
    assert '[0, 1]' in source
    assert '[0, 1, 2]' in source
    assert "report.error?.message" in source


def test_typescript_wrapper_exposes_command_specific_helpers() -> None:
    source = (
        ROOT / "packages" / "intentspec-ts" / "src" / "index.ts"
    ).read_text(encoding="utf-8")
    for snippet in (
        "validateJson",
        "inspectJson",
        "testJson",
        "compileText",
        "compileToFile",
        "doctorJson",
    ):
        assert snippet in source


def test_typescript_wrapper_manifest_includes_build_dependencies() -> None:
    package_json = json.loads(
        (ROOT / "packages" / "intentspec-ts" / "package.json").read_text(encoding="utf-8")
    )
    dev_dependencies = package_json["devDependencies"]
    assert "typescript" in dev_dependencies
    assert "@types/node" in dev_dependencies


def test_gitignore_ignores_node_modules() -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "node_modules/" in gitignore
