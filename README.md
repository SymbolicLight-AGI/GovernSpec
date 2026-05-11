# GovernSpec

[Read this in Chinese](README.zh-CN.md)

GovernSpec is a local-first contract compiler for AI agent workflows.

It lets you maintain one `govern.yaml` file and compile it into artifacts that existing tools can read, including `AGENTS.md`, `CLAUDE.md`, Cursor Rules, OpenAI Structured Outputs, Gemini structured output payloads, and MCP plans.

```text
govern.yaml
  -> validate
  -> resolve imports
  -> inspect normalized IIR
  -> compile to target artifacts
  -> run your agent
  -> test the output offline
```

> Define once, validate and compile everywhere.

GovernSpec does not call live LLM APIs, require API keys, or take over your agent runtime. It does three things:

- Defines task goals, permissions, constraints, human approval gates, output formats, and acceptance tests as a structured contract.
- Compiles that contract into formats used by different AI tools.
- Runs deterministic offline acceptance tests against the final agent output.

If this is your first time here, read this README first, then see [docs/technical-guide.md](docs/technical-guide.md).

## Naming Note

This project is not affiliated with `intentspec.org`, `JanneL/validate-intentspec-action`, or any third-party project with a similar name. When citing or discussing this repository, use **GovernSpec** or **GovernSpec v0.1 YAML contract toolchain**.

The current implementation uses `govern.yaml`, `GovernSpec` / `GovernPack`, Pydantic v2 schema models, IIR, target compilers, reverse importers, and an offline assertion runner. It is not an official implementation of an external GovernSpec standard.

## Who It Is For

### Engineering teams using several AI coding tools

If your team uses Cursor, Codex, Claude Code, API structured outputs, or similar tools, the same repository rules often get duplicated in several formats. GovernSpec keeps the source contract in one place and compiles it to the downstream files each tool expects.

### AI application developers

If your application needs stable JSON output, explicit model behavior limits, human approval points, or CI checks for output shape, GovernSpec provides a local schema, compiler, and test workflow.

### Security, governance, and compliance reviewers

If you care whether an agent may browse the web, write files, expose private data, or proceed without human confirmation, GovernSpec makes those boundaries explicit instead of burying them in prose prompts.

### Researchers and tool builders

GovernSpec includes a schema, IIR, importers, compilers, benchmark artifacts, and an offline assertion runner for studying artifact-level governance, round-trip fidelity, and task contract portability.

## What It Is Not

GovernSpec is not:

- an LLM runtime
- an agent orchestration framework
- a permission sandbox
- a runtime enforcement system
- an MCP replacement
- a replacement for Cursor, Codex, or Claude Code

It helps you express, distribute, and check rules. It does not guarantee that a model will obey those rules at runtime.

## What You Get

With GovernSpec, a team can maintain:

- one reviewable AI task contract
- downstream artifacts for multiple tools
- reusable governance packs with `GovernPack`
- explicit permission and human approval boundaries
- local or CI-friendly output acceptance tests
- a migration path from existing `AGENTS.md`, `CLAUDE.md`, Cursor Rules, or structured output JSON back to a contract draft
- visible target capability diagnostics, including constraints that cannot be fully represented in a given target

## Installation

GovernSpec requires Python 3.11 or newer.

Install from PyPI:

```bash
pip install governspec
```

Install from source:

```bash
git clone https://github.com/SymbolicLight-AGI/GovernSpec.git
cd GovernSpec
pip install -e ".[dev]"
```

Check the installation:

```bash
governspec doctor
```

The core GovernSpec workflow does not require an API key or network access.

## Five-Minute Quickstart

### 1. Create a contract

```bash
governspec init
```

To generate Chinese placeholder text:

```bash
governspec init --locale zh-CN
```

This creates `govern.yaml`. A minimal contract looks like this:

```yaml
version: "0.1"
kind: "GovernSpec"

metadata:
  name: "code_review"
  title: "Code review report"
  owner: "dev-team"

task:
  goal: "Review the codebase and produce a report without modifying files."
  priority: "high"

permissions:
  web: false
  filesystem:
    read: true
    write: false
  network: false
  tools:
    delete_file: false
    purchase: false

constraints:
  - "Do not fabricate facts."
  - "Do not modify existing code."

human_gates:
  - when: "A destructive action is required"
    action: "ask_confirmation"

output:
  format: "markdown"
  language: "en"
  max_words: 800
  sections:
    - "Summary"
    - "Findings"
    - "Testing"

tests:
  - name: "Must include all sections"
    assert:
      - type: "required_sections"
  - name: "Must stay concise"
    assert:
      - type: "max_words"
```

### 2. Validate the contract

```bash
governspec validate govern.yaml
```

`Validation status: ok` means the file passed schema and field validation.

### 3. Inspect the normalized representation

```bash
governspec inspect govern.yaml
```

`inspect` shows the IIR after imports, permission merging, and normalization. For scripts, use JSON output:

```bash
governspec inspect govern.yaml --format json
```

### 4. Compile to a target tool

Compile for Codex or other agents that read `AGENTS.md`:

```bash
governspec compile govern.yaml --target agents-md --out AGENTS.md
```

Compile for Claude Code:

```bash
governspec compile govern.yaml --target claude-md --out CLAUDE.md
```

Compile for Cursor:

```bash
governspec compile govern.yaml --target cursor-rules --out .
```

Compile for OpenAI Structured Outputs:

```bash
governspec compile govern.yaml --target openai-structured --out task.openai-structured.json
```

### 5. Run your agent

Run the agent in Cursor, Codex, Claude Code, or your API workflow as usual. GovernSpec does not replace that step.

### 6. Test the output offline

Save the agent output to a file such as `output.md`, then run:

```bash
governspec test govern.yaml --output output.md
```

Example result:

```text
Test status: ok
Passed:
- Must include all sections [required_sections]: All required sections are present.
- Must stay concise [max_words]: Estimated word count is within limit.
Failed: none
```

## Draft and Import

### Generate a draft from natural language

```bash
governspec draft "Review this repository without modifying code" --out draft.govern.yaml
governspec draft "Prepare a customer briefing, protect private data, and ask before using sensitive information" --out draft.govern.yaml
```

`draft` is a local heuristic generator. It does not call a live model. It is useful for bootstrapping, but the generated file should still be reviewed.

### Import from an existing artifact

```bash
governspec import AGENTS.md --out imported.govern.yaml
governspec import CLAUDE.md --out imported.govern.yaml
governspec import .cursor/rules/project.mdc --out imported.govern.yaml
governspec import task.openai-structured.json --out imported.govern.yaml
```

Supported sources:

| Source | Auto-detection signal |
| --- | --- |
| `agents-md` | `AGENTS.md` filename |
| `claude-md` | `CLAUDE.md` filename |
| `cursor-rules` | `.mdc` extension |
| `openai-structured` | `json_schema` key |
| `gemini-structured` | `generationConfig` key |

Imports produce drafts, not equivalence proofs. Natural-language artifacts lose information, so run `governspec validate` and `governspec inspect` after importing.

## GovernPack

Reusable governance rules can be stored as `GovernPack` files:

```yaml
# packs/privacy.govern.yaml
version: "0.1"
kind: "GovernPack"

metadata:
  name: "privacy_pack"
  description: "Privacy and PII protection rules"

constraints:
  - "Do not expose personal data."

permissions:
  web: false
  network: false

human_gates:
  - when: "Sensitive personal data is involved"
    action: "ask_confirmation"
```

Reference a pack from a task contract:

```yaml
imports:
  - "./packs/privacy.govern.yaml"
```

Import merging is conservative:

- local scalar fields win
- lists are merged and deduplicated
- permissions choose the stricter value, with deny winning
- imported acceptance assertions are not silently overwritten by local tests with the same name

## Compile Targets

| Target | Use case | Output |
| --- | --- | --- |
| `prompt` | Generic Markdown prompt | text |
| `agents-md` | Codex or repository instruction workflow | `AGENTS.md` |
| `claude-md` | Claude Code project memory | `CLAUDE.md` |
| `cursor-rules` | Cursor Project Rules | `.cursor/rules/governspec.mdc` |
| `antigravity-rules` | Antigravity-compatible repository rules | `.agents/rules/governspec.md` |
| `skill` | Generic skill bundle | `SKILL.md`, `references/`, `scripts/` |
| `openai-structured` | OpenAI Structured Outputs | JSON payload |
| `gemini-structured` | Gemini structured output | JSON payload |
| `mcp-plan` | MCP planning and inspection | JSON with risk and constraint-loss diagnostics |
| `openai-json` | Legacy transition payload | JSON payload |

See [docs/integrations.md](docs/integrations.md) for target-specific integration notes.

## Output Assertions

`governspec test` supports deterministic assertions:

| Assertion | Checks |
| --- | --- |
| `required_sections` | Markdown output contains all sections from `output.sections` |
| `contains` | output contains required text |
| `not_contains` | output does not contain forbidden text |
| `regex` | output matches a regular expression |
| `no_regex` | output does not match a forbidden regular expression |
| `max_words` | word count stays within `output.max_words` |
| `max_chars` | character count stays within the limit |
| `json_schema` | JSON output matches `output.schema` |
| `json_path_exists` | a JSON path exists |
| `json_array_min_items` | a JSON array has the required minimum size |

These assertions are meant for structure, format, length, and explicit text checks. They do not verify complex factual claims and do not replace human review.

## Common Workflows

### Code review

```bash
governspec examples --copy code_review.govern.yaml --out code_review.govern.yaml
governspec validate code_review.govern.yaml
governspec compile code_review.govern.yaml --target agents-md --out AGENTS.md
governspec test code_review.govern.yaml --output review.md
```

Use this to make an agent read-only, require fixed report sections, and prevent file modification.

### Structured JSON reports

```bash
governspec examples --copy report_json.govern.yaml --out report_json.govern.yaml
governspec compile report_json.govern.yaml --target openai-structured --out task.openai-structured.json
governspec test report_json.govern.yaml --output report_json.output.json
```

Use this for API workflows, machine-readable reports, and CI checks.

### Multi-tool rule synchronization

```bash
governspec compile govern.yaml --target agents-md --out AGENTS.md
governspec compile govern.yaml --target claude-md --out CLAUDE.md
governspec compile govern.yaml --target cursor-rules --out .
```

Use this when a repository is shared across Codex, Claude Code, and Cursor.

### CI checks

```bash
governspec validate govern.yaml
governspec compile govern.yaml --target agents-md --out /tmp/AGENTS.md
governspec test govern.yaml --output output.md
```

At minimum, CI should validate and compile important contracts.

## MCP Server

GovernSpec includes a thin MCP server:

```bash
governspec-mcp
```

Exposed tools:

- `governspec.validate`
- `governspec.inspect`
- `governspec.compile`
- `governspec.test`

Exposed resources:

- `govern://spec/<path>`
- `govern://iir/<path>`
- `govern://compiled/<target>/<path>`

`governspec-mcp` is an integration surface, not a runtime orchestration platform.

## Python SDK

Common document-level API:

```python
from pathlib import Path
from governspec_core import (
    load_document,
    resolve_document_imports,
    inspect_document,
    validate_document,
    compile_target,
    test_output,
    import_from_artifact,
    import_from_string,
    heuristic_draft_payload,
)

document = load_document(Path("govern.yaml"))
resolved = resolve_document_imports(document, Path("."))
report = validate_document(resolved)
payload = inspect_document(resolved)
```

For `GovernSpec`-only flows, use the narrower `load_spec`, `resolve_imports`, and `validate_spec` helpers.

## Repository Layout

```text
packages/governspec-core/   schema, parser, IIR, imports, targets, testing
packages/governspec-cli/    Typer CLI, governspec command
packages/governspec-mcp/    thin MCP server
packages/governspec-ts/     TypeScript package MVP
packages/governspec-vscode/ VS Code extension MVP
examples/                   runnable example contracts and outputs
schema/                     generated JSON Schema
benchmark/                  offline benchmark artifacts
docs/                       technical docs, migration guide, release notes
tests/                      pytest test suite
```

## Documentation

- [README.zh-CN.md](README.zh-CN.md): Simplified Chinese README.
- [docs/technical-guide.md](docs/technical-guide.md): detailed technical guide.
- [docs/integrations.md](docs/integrations.md): integration notes for supported tools.
- [docs/iir.md](docs/iir.md): Intermediate Intent Representation design.
- [docs/engineering/repository_file_map_zh.md](docs/engineering/repository_file_map_zh.md): repository file map in Chinese.
- [docs/migration-v0.1.md](docs/migration-v0.1.md): migration notes for the v0.1 schema.
- [docs/project-roadmap-zh.md](docs/project-roadmap-zh.md): project roadmap and progress notes in Chinese.
- [benchmark.md](benchmark.md): benchmark guide.
- [failure-cases.md](failure-cases.md): known failure cases and boundaries.

## Benchmark

Run the base benchmark:

```bash
python benchmark/run_benchmark.py
```

Run the reproducibility benchmark used by the research drafts:

```bash
python benchmark/reproducibility/scripts/run_all.py
```

Benchmarks do not call live LLM APIs. They evaluate local artifacts, compile behavior, round-trip import behavior, and deterministic tests.

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check .
mypy
```

Build release artifacts:

```bash
python -m build
twine check dist/*
```

Before contributing, read [CONTRIBUTING.md](CONTRIBUTING.md). Report security issues privately using [SECURITY.md](SECURITY.md). The project code of conduct is in [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

If you use GovernSpec in research, cite the software using the metadata in [CITATION.cff](CITATION.cff).

## Roadmap

### v0.2

- Better draft generation.
- More precise assertion auto-selection.
- Broader round-trip fidelity tests.
- Clearer target capability diagnostics.

### v0.3+

- Pack registry.
- Import traces.
- Workflow-level contract composition.
- IDE diagnostics.
- Optional model-based semantic evaluation.

## License

MIT. See [LICENSE](LICENSE).
