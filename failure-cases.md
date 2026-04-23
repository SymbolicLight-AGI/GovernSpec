# Failure Cases

Use this file to record real failures found while validating IntentSpec v0.1 on examples, benchmark tasks, private user tasks, or CI runs.

## Recording rules

- Add one entry per failure case.
- Preserve the exact command, error, and artifact paths.
- Link the failing spec, output artifact, and fix when available.
- Record whether the issue was caused by source authoring, import resolution, IIR normalization, target compilation, MCP integration, or acceptance testing.

## Entry Template

### FC-000

- Date:
- Owner:
- Status: `open` | `investigating` | `fixed` | `wontfix`
- Area: `parser` | `imports` | `iir` | `compiler` | `tester` | `cli` | `mcp` | `docs` | `benchmark`
- Source:
  - Example / user task / benchmark / CI / manual testing
- Intent file:
- Output file:
- Command:
  - `intent ...`
- Expected behavior:
- Actual behavior:
- Failed assertions or observed error:
- Constraint loss involved:
  - `yes` / `no`
- Impact:
  - Safety / usability / correctness / packaging / docs
- Root cause:
- Fix summary:
- Regression test added:
  - `yes` / `no`
- Follow-up:

## Failure Log

### FC-001

- Date:
- Owner:
- Status:
- Area:
- Source:
- Intent file:
- Output file:
- Command:
- Expected behavior:
- Actual behavior:
- Failed assertions or observed error:
- Constraint loss involved:
- Impact:
- Root cause:
- Fix summary:
- Regression test added:
- Follow-up:
