# GovernSpec Integrations

## Overview

Within this toolchain, `govern.yaml` is the source of truth for AI task contracts.
Downstream tools do not need to understand `govern.yaml` directly. They consume either:

- compiled files
- structured output payloads
- MCP surfaces

This keeps integration cost low and lets GovernSpec plug into existing ecosystems without introducing a new runtime.

## Integration Matrix

| Tool / Ecosystem | Integration path | Available GovernSpec artifacts |
| --- | --- | --- |
| Codex | instruction file + skills + MCP | `agents-md`, `skill`, `governspec-mcp` |
| Claude Code | instruction file + MCP | `claude-md`, `skill`, `governspec-mcp` |
| Cursor | project rules + MCP | `cursor-rules`, `skill`, `governspec-mcp` |
| VS Code Agent | project instructions + MCP + extension | `agents-md`, `skill`, `governspec-mcp`, VS Code extension MVP |
| OpenAI API | structured output payload | `openai-structured` |
| Gemini API | structured output payload | `gemini-structured` |
| Antigravity | filesystem-compatible rules + MCP | `antigravity-rules`, `skill`, `governspec-mcp` |

`skill` is a generic bundle target. It is not Codex-specific.

## Zero-Friction Targets

### `agents-md`

Use for Codex and other tools that read `AGENTS.md`-style repository instructions.

```bash
governspec compile examples/code_review.govern.yaml --target agents-md --out AGENTS.md
```

### `claude-md`

Use for Claude Code repositories that rely on `CLAUDE.md`.

```bash
governspec compile examples/code_review.govern.yaml --target claude-md --out CLAUDE.md
```

### `skill`

Use for generic skill-style bundles. The target itself is not Codex-specific.

```bash
governspec compile examples/code_review.govern.yaml --target skill --out ./review-skill
```

Generated files:

- `SKILL.md`
- `references/README.md`
- `scripts/README.md`

### `cursor-rules`

Use for Cursor project rules. The target emits a bundle rooted at the output directory.

```bash
governspec compile examples/code_review.govern.yaml --target cursor-rules --out .
```

Generated file:

- `.cursor/rules/governspec.mdc`

### `antigravity-rules`

Use for Antigravity-compatible repository rules. This target is filesystem-compatible and does not claim vendor certification.

```bash
governspec compile examples/code_review.govern.yaml --target antigravity-rules --out .
```

Generated file:

- `.agents/rules/governspec.md`

### `openai-structured`

Use for OpenAI Structured Outputs.

```bash
governspec compile examples/report_json.govern.yaml --target openai-structured --out task.openai-structured.json
```

### `gemini-structured`

Use for Gemini structured output payloads.

```bash
governspec compile examples/report_json.govern.yaml --target gemini-structured --out task.gemini-structured.json
```

This target only accepts a Gemini-compatible JSON Schema subset. Unsupported schema keywords fail compilation instead of degrading silently.

## Reverse Import

GovernSpec supports importing existing artifacts back into `govern.yaml` drafts. This reduces cold-start cost for teams that already have agent instructions, structured output payloads, or Cursor rules.

| Source artifact | Import type | Auto-detected |
| --- | --- | --- |
| `AGENTS.md` | `agents-md` | Yes (by filename) |
| `CLAUDE.md` | `claude-md` | Yes (by filename) |
| `.mdc` Cursor Rules | `cursor-rules` | Yes (by extension) |
| OpenAI Structured Outputs JSON | `openai-structured` | Yes (by `json_schema` key) |
| Gemini structured output JSON | `gemini-structured` | Yes (by `generationConfig` key) |

CLI usage:

```bash
governspec import AGENTS.md --out imported.govern.yaml
governspec import task.openai-structured.json --out imported.govern.yaml
```

SDK usage:

```python
from governspec_core import import_from_artifact, import_from_string

payload = import_from_artifact(Path("AGENTS.md"))
payload = import_from_string(json_text, "openai-structured")
```

The imported draft can then be validated, inspected, and compiled like any other `govern.yaml`.

## MCP Integration

`governspec-mcp` is the thin integration surface for MCP-capable clients.

```bash
governspec-mcp
```

### Codex Plugin Manifest

The repository includes a Codex plugin preview at `plugins/codex-governspec/`. Its manifest lives at `plugins/codex-governspec/.codex-plugin/plugin.json` and points Codex to:

- `./skills/` for the GovernSpec skill
- `./.mcp.json` for the local `python -m governspec_mcp.server` server

Before using the plugin, install GovernSpec and verify that the CLI and MCP module are available:

```bash
pip install governspec
governspec doctor
python -c "import governspec_mcp.server"
```

### Codex Plugin MCP Config

The Codex plugin preview in `plugins/codex-governspec/` includes a `.mcp.json` file that starts the local stdio server through the installed Python module:

```json
{
  "mcpServers": {
    "governspec": {
      "command": "python",
      "args": [
        "-m",
        "governspec_mcp.server"
      ]
    }
  }
}
```

The server resolves relative contract paths from the workspace directory used to start the MCP process.

### Tools

- `governspec.validate`
- `governspec.inspect`
- `governspec.compile`
- `governspec.test`

For Codex tool exposure, the server also provides underscore aliases:

- `governspec_validate`
- `governspec_inspect`
- `governspec_compile`
- `governspec_test`

### Resources

- `govern://spec/<path>`
- `govern://iir/<path>`
- `govern://compiled/<target>/<path>`

`govern://compiled/<target>/<path>` reads artifacts on demand:

- text targets return text content
- JSON targets return JSON text
- bundle targets return:

```json
{
  "kind": "bundle",
  "target": "cursor-rules",
  "files": {
    ".cursor/rules/governspec.mdc": "..."
  }
}
```

## VS Code Agent Strategy

GovernSpec does not introduce a VS Code-specific instruction target in this release.

The recommended path is:

1. compile repository instructions such as `AGENTS.md`
2. expose GovernSpec through `governspec-mcp`
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
