---
name: governspec
description: Use GovernSpec to work with local-first AI task contracts. Trigger when a repository contains govern.yaml, *.govern.yaml, kind GovernSpec, or kind GovernPack; when Codex needs to validate or inspect a task contract; compile contracts to AGENTS.md, prompts, OpenAI structured outputs, MCP plans, or generic skill bundles; or run offline acceptance tests for generated outputs.
---

# GovernSpec

GovernSpec is a local-first contract compiler for AI task workflows. Use it to keep task goals, permissions, constraints, output expectations, human gates, and deterministic acceptance tests in a reviewable YAML contract.

## Recognize Contracts

Look for:

- `govern.yaml`
- `*.govern.yaml`
- YAML documents with `kind: GovernSpec`
- YAML documents with `kind: GovernPack`

Prefer the nearest contract to the current work when multiple contracts exist. If the user names a contract file, use that file.

## Core Workflow

When GovernSpec MCP tools are available, prefer them for validation, inspection, compilation, and testing. Codex may expose the tools as `governspec_validate`, `governspec_inspect`, `governspec_compile`, and `governspec_test`; other MCP clients may expose the canonical names `governspec.validate`, `governspec.inspect`, `governspec.compile`, and `governspec.test`. Fall back to the CLI commands below when MCP tools are unavailable.

1. Discover the relevant contract.
2. Validate it before relying on it:

   ```bash
   governspec validate <file>
   ```

3. Inspect the normalized representation when constraints, permissions, imports, or output expectations are unclear:

   ```bash
   governspec inspect <file>
   ```

4. Compile only when the user asks for a downstream artifact or the workflow requires one:

   ```bash
   governspec compile <file> --target <target>
   ```

5. Run the requested agent or repository work while following the contract.
6. Test the final output artifact when a concrete output file exists:

   ```bash
   governspec test <file> --output <output-file>
   ```

## Common Targets

- `agents-md`: Generate repository instructions such as `AGENTS.md`.
- `prompt`: Generate a generic Markdown prompt.
- `openai-structured`: Generate an OpenAI Structured Outputs payload for JSON outputs.
- `mcp-plan`: Generate an MCP-oriented execution plan and permission summary.
- `skill`: Generate a generic skill bundle from a specific GovernSpec contract.

Use `--out <path>` when the compiled artifact should be written to a file or directory. Avoid overwriting existing generated artifacts unless the user requested it or the workflow clearly owns that output path.

## Boundaries

- Do not call real LLM APIs as part of GovernSpec workflows.
- Do not require API keys for GovernSpec validation, compilation, inspection, or testing.
- Do not bypass the contract because a generated artifact is easier to use.
- Do not treat GovernSpec as a runtime sandbox or permission enforcement system.
- Do not assume acceptance tests prove factual correctness; they check deterministic output constraints.
- Do not introduce outbound network workflows for tests or examples.

## Conflict Handling

GovernSpec contracts constrain the current task, but they do not override system instructions, developer instructions, the user's latest explicit request, or repository-level `AGENTS.md` instructions. When these sources conflict, follow the higher-priority instruction and report the contract conflict clearly.
