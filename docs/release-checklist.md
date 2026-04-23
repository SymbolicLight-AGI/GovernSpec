# Release Checklist

## Scope

This checklist is for IntentSpec v0.1 releases.

v0.1 is the mainline contract compiler release. The release should validate the multi-package repository, the v0.1 schema, the packaged examples, and the target compilers.

## Versioning and metadata

- Confirm the target version is updated in:
  - `pyproject.toml`
  - `packages/intentspec-core/src/intentspec_core/__init__.py`
  - `packages/intentspec-cli/src/intentspec/__init__.py`
- Confirm `README.md` reflects v0.1 behavior and command examples.
- Confirm `schema/intentspec.schema.json` is regenerated from the current v0.1 models.

## Validation

- Run `pip install -e ".[dev]"`.
- Run `pytest`.
- Run `ruff check .`.
- Run `mypy`.
- Run `python -m build`.
- Run `twine check dist/*`.
- Run `npm install && npm run build` in `packages/intentspec-ts`.
- Run `npm install && npm run build` in `packages/intentspec-vscode`.

## CLI sanity checks

- Run `intent doctor`.
- Run `intent examples`.
- Run `intent validate examples/customer_brief.intent.yaml --format json`.
- Run `intent inspect examples/customer_brief.intent.yaml --format json`.
- Run `intent compile examples/report_json.intent.yaml --target openai-structured`.
- Run `intent compile examples/code_review.intent.yaml --target agents-md`.
- Run `intent compile examples/imported_customer_brief.intent.yaml --target mcp-plan`.
- Run `intent test examples/report_json.intent.yaml --output examples/report_json.output.json --format json`.
- Run `intent draft "Review this repository" --out /tmp/draft-test.intent.yaml` and verify output.
- Run `intent import` round-trip: compile an example to `agents-md`, then import it back.
  - `intent compile examples/code_review.intent.yaml --target agents-md --out /tmp/test-agents.md`
  - `intent import /tmp/test-agents.md --out /tmp/test-imported.intent.yaml`
  - `intent validate /tmp/test-imported.intent.yaml`
- Run `intent import` with each supported source type: `agents-md`, `claude-md`, `cursor-rules`, `openai-structured`, `gemini-structured`.

## Example checks

- Validate every valid `.intent.yaml` example under `examples/`.
- Confirm expected-failure examples such as `invalid_*` still fail validation with clear errors.
- Confirm `examples/imported_customer_brief.intent.yaml` still resolves `examples/packs/*`.
- Confirm `examples/report_json.intent.yaml` covers `output.schema` and JSON assertions.
- Confirm packaged examples exposed by `intent examples` are still current.

## Documentation checks

- Review `README.md` for stale references to `0.1.x`.
- Review `docs/iir.md` for consistency with the implemented IIR.
- Review `docs/migration-v0.1.md` for accuracy (including reverse import section).
- Review `docs/integrations.md` for accuracy (including reverse import matrix).
- Review `benchmark.md` and `failure-cases.md` templates for current v0.1 terminology.

## Benchmark checks

- Run `python benchmark/run_benchmark.py`.
- Confirm benchmark tasks cover:
  - markdown task
  - strict JSON task
  - imported pack task
- Confirm benchmark outputs still pass acceptance tests.

## Packaging checks

- Confirm package data includes recursive example resources.
- Confirm `intent` entry point resolves to the CLI package.
- Confirm `intentspec-mcp` entry point starts the thin MCP server.
- Confirm `packages/intentspec-ts` still builds successfully.
- Confirm `packages/intentspec-vscode` still builds successfully.

## Final release decision

Release only if:

- build and metadata checks pass
- examples are current
- benchmark is green
- schema is regenerated
- migration notes are updated
