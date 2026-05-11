# GovernSpec v0.1.0

GovernSpec v0.1.0 is the current mainline release of a local-first, deterministic, embeddable YAML task contract compiler.

## What’s new

- First-class strict JSON contracts with `output.schema`
- Reusable policy packs with `imports` and `GovernPack`
- Normalized IIR inspection via `governspec inspect`
- New compile targets:
  - `openai-structured`
  - `gemini-structured`
  - `agents-md`
  - `claude-md`
  - `cursor-rules`
  - `antigravity-rules`
  - `skill`
- Enhanced `mcp-plan` with:
  - `required_user_consents`
  - `sensitive_resources`
  - `risk_level`
  - `constraint_loss`
- Thin MCP server for:
  - `governspec.validate`
  - `governspec.inspect`
  - `governspec.compile`
  - `governspec.test`
- VS Code extension MVP in `packages/governspec-vscode`
- Experimental `governspec draft` with deterministic heuristic generation (Chinese + English, permission/constraint/gate inference)
- `governspec import` reverse-imports existing artifacts (`agents-md`, `claude-md`, `cursor-rules`, `openai-structured`, `gemini-structured`) into `govern.yaml` drafts

## Validation

Release validation completed successfully:

- `pip install -e ".[dev]"`
- `pytest` → `210 passed`
- `ruff check .`
- `mypy`
- `python -m build`
- `twine check dist/*`
- `npm install --no-package-lock && npm run build` in `packages/governspec-ts`
- `npm install --no-package-lock && npm run build` in `packages/governspec-vscode`
- benchmark pass rate → `100.0%`

## Recommended quick start

```bash
governspec doctor
governspec examples
governspec validate examples/customer_brief.govern.yaml
governspec inspect examples/customer_brief.govern.yaml --format json
governspec compile examples/report_json.govern.yaml --target openai-structured --out task.openai-structured.json
governspec compile examples/code_review.govern.yaml --target agents-md --out AGENTS.md
governspec test examples/report_json.govern.yaml --output examples/report_json.output.json --format json
governspec draft "Generate a privacy-safe customer brief"
governspec import AGENTS.md --out imported.govern.yaml
```

## Upgrade notes

- `v0.1` is the supported mainline schema.
- Pre-release or draft-era task files should be aligned with the current examples and schema.
- `openai-json` remains available as a legacy transitional target.
- See migration guide, replace `<owner>/<repo>` before publishing:
  - [docs/migration-v0.1.md](https://github.com/<owner>/<repo>/blob/main/docs/migration-v0.1.md)

## Suggested tag

`v0.1.0`
