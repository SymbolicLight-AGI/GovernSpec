# Migrating to GovernSpec 0.1

## Summary

GovernSpec v0.1 is the current supported schema line.

Use this guide if you have pre-release drafts, internal prototypes, or older task files that do not yet follow the v0.1 schema, and you want to align them with the current examples, CLI, and schema artifact.

## Top-level changes

### Version

Use:

```yaml
version: "0.1"
```

### Kind

`GovernSpec` remains valid for full task contracts.

v0.1 also supports:

```yaml
kind: "GovernPack"
```

Use `GovernPack` for reusable governance layers such as privacy packs, no-network packs, and shared output policy packs.

## Capability: `imports`

v0.1 supports:

```yaml
imports:
  - "./packs/privacy.govern.yaml"
  - "./packs/no-network.govern.yaml"
```

Imports are resolved depth-first, left-to-right, and merged before local fields are applied.

### Merge rules

- scalar values: local wins
- dictionaries: deep merge
- lists: merged and deduplicated
- `tests`: local test with the same `name` replaces imported test
- `human_gates`: deduplicated by `(when, action)`
- `permissions`: `deny wins`

## Capability: `output.schema`

Strict JSON output contracts are first-class in v0.1:

```yaml
output:
  format: "json"
  schema:
    type: object
    required:
      - verdict
    properties:
      verdict:
        type: string
```

This is the source for:

- local JSON acceptance testing
- `openai-structured`
- IIR output contracts

## Assertions

v0.1 includes:

- `json_schema`
- `json_path_exists`
- `json_array_min_items`

Example:

```yaml
tests:
  - name: "Must match schema"
    assert:
      - type: "json_schema"
  - name: "Need at least 3 risks"
    assert:
      - type: "json_array_min_items"
        path: "$.risks"
        value: 3
```

## Command: `inspect`

v0.1 includes:

```bash
governspec inspect examples/customer_brief.govern.yaml --format json
```

This exposes the normalized IIR used by target compilers.

## Compile targets

### `openai-structured`

Recommended replacement for schema-driven JSON output integration.

### `agents-md`

Compiles a contract into an `AGENTS.md` style instruction document for coding agents.

### `skill`

Compiles a contract into a minimal reusable skill bundle with `SKILL.md`, `references/`, and `scripts/`.

## `mcp-plan` changes

`mcp-plan` is now a safety-oriented execution plan and includes:

- `required_user_consents`
- `sensitive_resources`
- `risk_level`
- `constraint_loss`

## Experimental draft generation

v0.1 includes:

```bash
governspec draft "help me prepare a privacy-safe customer brief"
```

This feature is intentionally:

- local-first
- heuristic
- deterministic
- non-provider-backed

It generates a draft contract only. It does not execute tasks.

## Before and after example

### Current v0.1 style

```yaml
version: "0.1"
kind: "GovernSpec"

task:
  goal: "Generate a customer brief"

output:
  format: "markdown"
  language: "zh-CN"
  max_words: 800
  sections:
    - "Summary"
```

### 0.2 style

```yaml
version: "0.1"
kind: "GovernSpec"

imports:
  - "./packs/privacy.govern.yaml"

task:
  goal: "Generate a customer brief"

output:
  format: "markdown"
  language: "zh-CN"
  max_words: 800
  sections:
    - "Summary"
```

## Reverse import existing artifacts

If you already have `AGENTS.md`, `CLAUDE.md`, Cursor Rules, or structured output payloads, you can use `governspec import` to generate an `govern.yaml` draft automatically:

```bash
governspec import AGENTS.md --out imported.govern.yaml
governspec import CLAUDE.md --type claude-md --out imported.govern.yaml
governspec import .cursor/rules/governspec.mdc --out imported.govern.yaml
governspec import task.openai-structured.json --out imported.govern.yaml
```

The importer will:

- auto-detect the source type from file name and content (or use `--type` to specify explicitly)
- extract goal, constraints, permissions, human gates, output spec, and tests
- produce a ready-to-review `govern.yaml` draft

This is the recommended starting point for teams migrating from hand-written agent instructions to GovernSpec contracts.

## Recommended migration flow

1. Import existing artifacts with `governspec import` (if applicable).
2. Update `version` to `0.1`.
3. Extract shared constraints into `GovernPack` files.
4. Replace duplicated policy sections with `imports`.
5. If the output should be strict JSON, move to `output.schema`.
6. Add `json_schema` assertions for JSON tasks.
7. Run:

```bash
governspec validate <file>
governspec inspect <file> --format json
governspec test <file> --output <artifact>
```

## Unsupported migration assumptions

GovernSpec v0.1 does not promise long-term parallel support for v0.1 runtime behavior. Keep old files only as historical references or convert them to 0.2.
