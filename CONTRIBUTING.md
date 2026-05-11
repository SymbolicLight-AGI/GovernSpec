# Contributing to GovernSpec

Thank you for helping improve GovernSpec. The project is intentionally local-first,
deterministic, and small enough to inspect.

When writing public-facing material, prefer "GovernSpec" for
this repository. Do not describe the project as an official implementation of
`intentspec.org` or of any similarly named third-party tool.

## Development Setup

Use Python 3.11 or newer.

```bash
pip install -e ".[dev]"
```

Run the local verification suite before opening a pull request:

```bash
pytest
ruff check .
mypy
python -m build
```

## Issue Reports

Please include:

- the GovernSpec version or commit hash,
- your Python version and operating system,
- the command you ran,
- a minimal `govern.yaml` or output sample when possible,
- the expected behavior and actual behavior.

Do not include API keys, secrets, private customer data, or proprietary prompts in
issues.

## Pull Requests

Before changing behavior, add or update tests that demonstrate the expected result.
Keep changes focused and avoid mixing unrelated refactors with feature work.

GovernSpec does not call real LLM APIs in tests. New tests should remain offline,
deterministic, and independent of real API keys.

## Coding Guidelines

- Use Python 3.11+ type annotations.
- Prefer small, readable functions.
- Keep public CLI behavior aligned with the README and examples.
- When changing model fields, update examples, schema, documentation, and tests
  together.
- Keep comments in source files concise and in English.

## Support

Use GitHub issues for bug reports, feature requests, and support questions once the
public repository is available.
