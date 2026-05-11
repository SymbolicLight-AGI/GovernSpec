# Release Checklist

## Scope

This checklist is for GovernSpec v0.1 releases.

v0.1 is the mainline contract compiler release. The release should validate the multi-package repository, the v0.1 schema, the packaged examples, and the target compilers.

## Versioning and metadata

- Confirm the target version is updated in:
  - `pyproject.toml`
  - `packages/governspec-core/src/governspec_core/__init__.py`
  - `packages/governspec-cli/src/governspec/__init__.py`
- Confirm `README.md` reflects v0.1 behavior and command examples.
- Confirm `schema/governspec.schema.json` is regenerated from the current v0.1 models.

## Validation

- Run `pip install -e ".[dev]"`.
- Run `pytest`.
- Run `ruff check .`.
- Run `mypy`.
- Run `python -m build`.
- Run `twine check dist/*`.
- Run `npm install && npm run build` in `packages/governspec-ts`.
- Run `npm install && npm run build` in `packages/governspec-vscode`.

## CLI sanity checks

- Run `governspec doctor`.
- Run `governspec examples`.
- Run `governspec validate examples/customer_brief.govern.yaml --format json`.
- Run `governspec inspect examples/customer_brief.govern.yaml --format json`.
- Run `governspec compile examples/report_json.govern.yaml --target openai-structured`.
- Run `governspec compile examples/code_review.govern.yaml --target agents-md`.
- Run `governspec compile examples/imported_customer_brief.govern.yaml --target mcp-plan`.
- Run `governspec test examples/report_json.govern.yaml --output examples/report_json.output.json --format json`.
- Run `governspec draft "Review this repository" --out /tmp/draft-test.govern.yaml` and verify output.
- Run `governspec import` round-trip: compile an example to `agents-md`, then import it back.
  - `governspec compile examples/code_review.govern.yaml --target agents-md --out /tmp/test-agents.md`
  - `governspec import /tmp/test-agents.md --out /tmp/test-imported.govern.yaml`
  - `governspec validate /tmp/test-imported.govern.yaml`
- Run `governspec import` with each supported source type: `agents-md`, `claude-md`, `cursor-rules`, `openai-structured`, `gemini-structured`.

## Example checks

- Validate every valid `.govern.yaml` example under `examples/`.
- Confirm expected-failure examples such as `invalid_*` still fail validation with clear errors.
- Confirm `examples/imported_customer_brief.govern.yaml` still resolves `examples/packs/*`.
- Confirm `examples/report_json.govern.yaml` covers `output.schema` and JSON assertions.
- Confirm packaged examples exposed by `governspec examples` are still current.

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
- Confirm `governspec` entry point resolves to the CLI package.
- Confirm `governspec-mcp` entry point starts the thin MCP server.
- Confirm `packages/governspec-ts` still builds successfully.
- Confirm `packages/governspec-vscode` still builds successfully.

## Final release decision

Release only if:

- build and metadata checks pass
- examples are current
- benchmark is green
- schema is regenerated
- migration notes are updated
