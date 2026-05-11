# AGENTS.md

## Project goal

GovernSpec is a local-first CLI and schema for describing AI tasks as explicit contracts.

## Setup

- Install dependencies: `pip install -e ".[dev]"`
- Run tests: `pytest`
- Run CLI locally: `governspec --help`

## Architecture

- `governspec_core.spec` — YAML parser, Pydantic models, and schema generation
- `governspec_core.iir` — Intermediate Intent Representation builder
- `governspec_core.targets` — compile-to-target logic (agents-md, openai-structured, etc.)
- `governspec_core.importers` — reverse import from existing artifacts (AGENTS.md, Cursor Rules, OpenAI/Gemini JSON)
- `governspec_core.draft` — enhanced heuristic draft generator (CJK + English)
- `governspec_core.testing` — offline acceptance test runner
- `governspec_cli` — Typer CLI (`governspec` command)
- `governspec_mcp` — thin MCP server

## Code style

- Use Python 3.11+ with type annotations.
- Keep the MVP local, deterministic, and easy to test.
- Prefer small, surgical changes over speculative abstractions.
- Use Pydantic v2 models and Typer CLI patterns consistently.
- Centralize shared logic (e.g. `_parsing.py` for importers, `build_draft_payload` for payload construction).
- Pattern tuples in heuristic modules should only carry elements that are actually used.

## Safety boundaries

- Do not call real LLM APIs.
- Do not require network access in tests.
- Do not introduce real outbound network workflows.
- Do not make examples depend on real API keys.
- Do not add automatic high-risk actions.

## Maintenance rules

- Add or update tests for every behavior change.
- When changing model fields, update examples, JSON schema, README, and tests together.
- Keep CLI behavior aligned with the documented acceptance criteria.
