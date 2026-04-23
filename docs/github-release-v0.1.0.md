# IntentSpec v0.1.0

IntentSpec v0.1.0 is the current mainline release of a local-first, deterministic, embeddable task contract compiler.

## What’s new

- First-class strict JSON contracts with `output.schema`
- Reusable policy packs with `imports` and `IntentPack`
- Normalized IIR inspection via `intent inspect`
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
  - `intentspec.validate`
  - `intentspec.inspect`
  - `intentspec.compile`
  - `intentspec.test`
- VS Code extension MVP in `packages/intentspec-vscode`
- Experimental `intent draft` with deterministic heuristic generation (Chinese + English, permission/constraint/gate inference)
- `intent import` reverse-imports existing artifacts (`agents-md`, `claude-md`, `cursor-rules`, `openai-structured`, `gemini-structured`) into `intent.yaml` drafts

## Validation

Release validation completed successfully:

- `pip install -e ".[dev]"`
- `pytest` → `210 passed`
- `ruff check .`
- `mypy`
- `python -m build`
- `twine check dist/*`
- `npm install --no-package-lock && npm run build` in `packages/intentspec-ts`
- `npm install --no-package-lock && npm run build` in `packages/intentspec-vscode`
- benchmark pass rate → `100.0%`

## Recommended quick start

```bash
intent doctor
intent examples
intent validate examples/customer_brief.intent.yaml
intent inspect examples/customer_brief.intent.yaml --format json
intent compile examples/report_json.intent.yaml --target openai-structured --out task.openai-structured.json
intent compile examples/code_review.intent.yaml --target agents-md --out AGENTS.md
intent test examples/report_json.intent.yaml --output examples/report_json.output.json --format json
intent draft "Generate a privacy-safe customer brief"
intent import AGENTS.md --out imported.intent.yaml
```

## Upgrade notes

- `v0.1` is the supported mainline schema.
- Pre-release or draft-era task files should be aligned with the current examples and schema.
- `openai-json` remains available as a legacy transitional target.
- See migration guide, replace `<owner>/<repo>` before publishing:
  - [docs/migration-v0.1.md](https://github.com/<owner>/<repo>/blob/main/docs/migration-v0.1.md)

## Suggested tag

`v0.1.0`
