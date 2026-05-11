# GovernSpec v0.1.0 Release Notes

Release date: 2026-04-23

Recommended git tag: `v0.1.0`

## Summary

GovernSpec v0.1.0 is the current mainline release.

This release moves the project from a handwritten YAML validator to a local-first, deterministic, embeddable task contract compiler.

GovernSpec does not introduce a real LLM runtime, web UI, database, or MCP orchestration layer in this release. The focus remains on the contract layer, target compilation, offline validation, and release readiness.

## Highlights

- `output.schema` is now first-class for strict JSON contracts.
- `imports` and `GovernPack` support reusable governance layers.
- `governspec inspect` exposes the normalized IIR used by compilers.
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
  - `governspec.validate`
  - `governspec.inspect`
  - `governspec.compile`
  - `governspec.test`
- VS Code extension MVP included:
  - `packages/governspec-vscode`
- `governspec draft` is available as an experimental, heuristic, deterministic draft generator.
  - Supports Chinese and English prompts.
  - Infers permissions, constraints, human gates, output format, and sections from free text.
- `governspec import` reverse-imports existing artifacts into `govern.yaml` drafts:
  - Supported source types: `agents-md`, `claude-md`, `cursor-rules`, `openai-structured`, `gemini-structured`.
  - Auto-detects source type from file name and content when `--type` is omitted.
  - Precise parsing for GovernSpec-generated documents; heuristic parsing for hand-written documents.
- Python SDK now exports `SUPPORTED_IMPORT_TYPES`, `import_from_artifact`, `import_from_string`, and `heuristic_draft_payload`.

## Packaging and repository changes

- The repository now uses a multi-package layout:
  - `packages/governspec-core`
  - `packages/governspec-cli`
  - `packages/governspec-mcp`
  - `packages/governspec-ts`
  - `packages/governspec-vscode`
- The public CLI command remains `governspec`.
- The published schema artifact is:
  - `schema/governspec.schema.json`

## Breaking and compatibility notes

- `v0.1` is the supported mainline schema.
- Pre-release or draft-era task files should be aligned with the current v0.1 schema and examples.
- Migration guidance is documented in:
  - [migration-v0.1.md](/D:/GovernSpec/docs/migration-v0.1.md)
- `openai-json` is still available, but it is a legacy transitional target. `openai-structured` is the recommended JSON integration target.

## Validation summary

The following release checks were run before preparing this release:

- `pip install -e ".[dev]"`
- `pytest`
- `ruff check .`
- `mypy`
- `python -m build`
- `twine check dist/*`
- `npm install --no-package-lock && npm run build` in `packages/governspec-ts`
- `npm install --no-package-lock && npm run build` in `packages/governspec-vscode`
- `governspec doctor`
- `governspec examples`
- `governspec validate examples/customer_brief.govern.yaml --format json`
- `governspec inspect examples/customer_brief.govern.yaml --format json`
- `governspec validate examples/packs/privacy.govern.yaml --format json`
- `governspec inspect examples/packs/privacy.govern.yaml --format json`
- `governspec compile examples/report_json.govern.yaml --target openai-structured`
- `governspec compile examples/report_json.govern.yaml --target gemini-structured`
- `governspec compile examples/code_review.govern.yaml --target agents-md`
- `governspec compile examples/code_review.govern.yaml --target claude-md`
- `governspec compile examples/code_review.govern.yaml --target cursor-rules`
- `governspec compile examples/code_review.govern.yaml --target antigravity-rules`
- `governspec compile examples/imported_customer_brief.govern.yaml --target mcp-plan`
- `governspec test examples/report_json.govern.yaml --output examples/report_json.output.json --format json`
- `governspec import` round-trip checks for all 5 supported source types
- `governspec draft` heuristic generation checks for Chinese and English prompts
- MCP smoke checks for `initialize`, compiled resources, and `governspec.test`
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
2. Extract shared rules into `GovernPack` files when appropriate.
3. Use `output.schema` for strict JSON tasks.
4. Replace `openai-json` with `openai-structured` where possible.
5. Use `governspec inspect` to review normalized IIR before integrating targets.

## Suggested release commands

```bash
git status
git tag -a v0.1.0 -m "GovernSpec v0.1.0"
git push origin v0.1.0
```

## Non-goals reaffirmed

GovernSpec v0.1.0 does not add:

- real LLM API execution
- MCP runtime orchestration
- Web UI
- database storage
- automatic high-risk action execution
- LangGraph, DSPy, or BAML adapters
