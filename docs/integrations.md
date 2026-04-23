# IntentSpec Integrations

## Overview

IntentSpec is the upstream source-of-truth for AI task contracts.

Downstream tools do not need to understand `intent.yaml` directly. They consume either:

- compiled files
- structured output payloads
- MCP surfaces

This keeps integration cost low and lets IntentSpec plug into existing ecosystems without introducing a new runtime.

## Integration Matrix

| Tool / Ecosystem | Integration path | Available IntentSpec artifacts |
| --- | --- | --- |
| Codex | instruction file + skills + MCP | `agents-md`, `skill`, `intentspec-mcp` |
| Claude Code | instruction file + MCP | `claude-md`, `skill`, `intentspec-mcp` |
| Cursor | project rules + MCP | `cursor-rules`, `skill`, `intentspec-mcp` |
| VS Code Agent | project instructions + MCP + extension | `agents-md`, `skill`, `intentspec-mcp`, VS Code extension MVP |
| OpenAI API | structured output payload | `openai-structured` |
| Gemini API | structured output payload | `gemini-structured` |
| Antigravity | filesystem-compatible rules + MCP | `antigravity-rules`, `skill`, `intentspec-mcp` |

`skill` is a generic bundle target. It is not Codex-specific.

## Zero-Friction Targets

### `agents-md`

Use for Codex and other tools that read `AGENTS.md`-style repository instructions.

```bash
intent compile examples/code_review.intent.yaml --target agents-md --out AGENTS.md
```

### `claude-md`

Use for Claude Code repositories that rely on `CLAUDE.md`.

```bash
intent compile examples/code_review.intent.yaml --target claude-md --out CLAUDE.md
```

### `skill`

Use for generic skill-style bundles. The target itself is not Codex-specific.

```bash
intent compile examples/code_review.intent.yaml --target skill --out ./review-skill
```

Generated files:

- `SKILL.md`
- `references/README.md`
- `scripts/README.md`

### `cursor-rules`

Use for Cursor project rules. The target emits a bundle rooted at the output directory.

```bash
intent compile examples/code_review.intent.yaml --target cursor-rules --out .
```

Generated file:

- `.cursor/rules/intentspec.mdc`

### `antigravity-rules`

Use for Antigravity-compatible repository rules. This target is filesystem-compatible and does not claim vendor certification.

```bash
intent compile examples/code_review.intent.yaml --target antigravity-rules --out .
```

Generated file:

- `.agents/rules/intentspec.md`

### `openai-structured`

Use for OpenAI Structured Outputs.

```bash
intent compile examples/report_json.intent.yaml --target openai-structured --out task.openai-structured.json
```

### `gemini-structured`

Use for Gemini structured output payloads.

```bash
intent compile examples/report_json.intent.yaml --target gemini-structured --out task.gemini-structured.json
```

This target only accepts a Gemini-compatible JSON Schema subset. Unsupported schema keywords fail compilation instead of degrading silently.

## Reverse Import

IntentSpec supports importing existing artifacts back into `intent.yaml` drafts. This reduces cold-start cost for teams that already have agent instructions, structured output payloads, or Cursor rules.

| Source artifact | Import type | Auto-detected |
| --- | --- | --- |
| `AGENTS.md` | `agents-md` | Yes (by filename) |
| `CLAUDE.md` | `claude-md` | Yes (by filename) |
| `.mdc` Cursor Rules | `cursor-rules` | Yes (by extension) |
| OpenAI Structured Outputs JSON | `openai-structured` | Yes (by `json_schema` key) |
| Gemini structured output JSON | `gemini-structured` | Yes (by `generationConfig` key) |

CLI usage:

```bash
intent import AGENTS.md --out imported.intent.yaml
intent import task.openai-structured.json --out imported.intent.yaml
```

SDK usage:

```python
from intentspec_core import import_from_artifact, import_from_string

payload = import_from_artifact(Path("AGENTS.md"))
payload = import_from_string(json_text, "openai-structured")
```

The imported draft can then be validated, inspected, and compiled like any other `intent.yaml`.

## MCP Integration

`intentspec-mcp` is the thin integration surface for MCP-capable clients.

```bash
intentspec-mcp
```

### Tools

- `intentspec.validate`
- `intentspec.inspect`
- `intentspec.compile`
- `intentspec.test`

### Resources

- `intent://spec/<path>`
- `intent://iir/<path>`
- `intent://compiled/<target>/<path>`

`intent://compiled/<target>/<path>` reads artifacts on demand:

- text targets return text content
- JSON targets return JSON text
- bundle targets return:

```json
{
  "kind": "bundle",
  "target": "cursor-rules",
  "files": {
    ".cursor/rules/intentspec.mdc": "..."
  }
}
```

## VS Code Agent Strategy

IntentSpec does not introduce a VS Code-specific instruction target in this release.

The recommended path is:

1. compile repository instructions such as `AGENTS.md`
2. expose IntentSpec through `intentspec-mcp`
3. use the lightweight VS Code extension MVP

This keeps the integration aligned with existing VS Code Agent and MCP workflows without adding a parallel DSL.

## Non-Goals

This release does not add:

- a Copilot-specific target
- a Cursor plugin
- a Claude plugin
- an Antigravity workflow generator
- a real LLM runtime
- runtime orchestration for MCP tools
