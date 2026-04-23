# IntentSpec v0.1.0 Release Notes

Release date: 2026-04-23

Recommended git tag: `v0.1.0`

## Summary

IntentSpec v0.1.0 is the current mainline release.

This release moves the project from a handwritten YAML validator to a local-first, deterministic, embeddable task contract compiler.

IntentSpec does not introduce a real LLM runtime, web UI, database, or MCP orchestration layer in this release. The focus remains on the contract layer, target compilation, offline validation, and release readiness.

## Highlights

- `output.schema` is now first-class for strict JSON contracts.
- `imports` and `IntentPack` support reusable governance layers.
- `intent inspect` exposes the normalized IIR used by compilers.
- New compile targets:
  - `openai-structured`
  - `gemini-structured`
  - `agents-md`
  - `claude-md`
  - `cursor-rules`
  - `antigravity-rules`
  - `skill`
- `mcp-plan` now includes:
  - `required_user_consents`
  - `sensitive_resources`
  - `risk_level`
  - `constraint_loss`
- Thin MCP server included:
  - `intentspec.validate`
  - `intentspec.inspect`
  - `intentspec.compile`
  - `intentspec.test`
- VS Code extension MVP included:
  - `packages/intentspec-vscode`
- `intent draft` is available as an experimental, heuristic, deterministic draft generator.
  - Supports Chinese and English prompts.
  - Infers permissions, constraints, human gates, output format, and sections from free text.
- `intent import` reverse-imports existing artifacts into `intent.yaml` drafts:
  - Supported source types: `agents-md`, `claude-md`, `cursor-rules`, `openai-structured`, `gemini-structured`.
  - Auto-detects source type from file name and content when `--type` is omitted.
  - Precise parsing for IntentSpec-generated documents; heuristic parsing for hand-written documents.
- Python SDK now exports `SUPPORTED_IMPORT_TYPES`, `import_from_artifact`, `import_from_string`, and `heuristic_draft_payload`.

## Packaging and repository changes

- The repository now uses a multi-package layout:
  - `packages/intentspec-core`
  - `packages/intentspec-cli`
  - `packages/intentspec-mcp`
  - `packages/intentspec-ts`
  - `packages/intentspec-vscode`
- The public CLI command remains `intent`.
- The published schema artifact is:
  - `schema/intentspec.schema.json`

## Breaking and compatibility notes

- `v0.1` is the supported mainline schema.
- Pre-release or draft-era task files should be aligned with the current v0.1 schema and examples.
- Migration guidance is documented in:
  - [migration-v0.1.md](/D:/IntentSpec/docs/migration-v0.1.md)
- `openai-json` is still available, but it is a legacy transitional target. `openai-structured` is the recommended JSON integration target.

## Validation summary

The following release checks were run before preparing this release:

- `pip install -e ".[dev]"`
- `pytest`
- `ruff check .`
- `mypy`
- `python -m build`
- `twine check dist/*`
- `npm install --no-package-lock && npm run build` in `packages/intentspec-ts`
- `npm install --no-package-lock && npm run build` in `packages/intentspec-vscode`
- `intent doctor`
- `intent examples`
- `intent validate examples/customer_brief.intent.yaml --format json`
- `intent inspect examples/customer_brief.intent.yaml --format json`
- `intent validate examples/packs/privacy.intent.yaml --format json`
- `intent inspect examples/packs/privacy.intent.yaml --format json`
- `intent compile examples/report_json.intent.yaml --target openai-structured`
- `intent compile examples/report_json.intent.yaml --target gemini-structured`
- `intent compile examples/code_review.intent.yaml --target agents-md`
- `intent compile examples/code_review.intent.yaml --target claude-md`
- `intent compile examples/code_review.intent.yaml --target cursor-rules`
- `intent compile examples/code_review.intent.yaml --target antigravity-rules`
- `intent compile examples/imported_customer_brief.intent.yaml --target mcp-plan`
- `intent test examples/report_json.intent.yaml --output examples/report_json.output.json --format json`
- `intent import` round-trip checks for all 5 supported source types
- `intent draft` heuristic generation checks for Chinese and English prompts
- MCP smoke checks for `initialize`, compiled resources, and `intentspec.test`
- `python benchmark/run_benchmark.py`

Observed results:

- `pytest`: `210 passed`
- `benchmark`:
  - `Total tasks: 3`
  - `Passed: 3`
  - `Pass rate: 100.0%`
  - `Constraint loss count: 6`

## Upgrade checklist for users

If you are upgrading from pre-release or draft-era usage:

1. Move your specs to `version: "0.1"`.
2. Extract shared rules into `IntentPack` files when appropriate.
3. Use `output.schema` for strict JSON tasks.
4. Replace `openai-json` with `openai-structured` where possible.
5. Use `intent inspect` to review normalized IIR before integrating targets.

## Suggested release commands

```bash
git status
git tag -a v0.1.0 -m "IntentSpec v0.1.0"
git push origin v0.1.0
```

## Non-goals reaffirmed

IntentSpec v0.1.0 does not add:

- real LLM API execution
- MCP runtime orchestration
- Web UI
- database storage
- automatic high-risk action execution
- LangGraph, DSPy, or BAML adapters
