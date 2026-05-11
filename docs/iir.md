# Intent Intermediate Representation (IIR)

## Overview

Intent Intermediate Representation, abbreviated as IIR, is the normalized internal contract form used by GovernSpec v0.1.

In v0.1, the compiler pipeline is:

```text
govern.yaml
  -> load spec
  -> resolve imports
  -> normalize to IIR
  -> compile target
```

This means the project is no longer a thin YAML-to-template tool. It now has an explicit compiler middle layer.

## Why IIR exists

### Stable normalization

The author-facing YAML format is optimized for readability and review. Target artifacts such as prompts, `AGENTS.md`, Structured Outputs payloads, and MCP execution plans are optimized for downstream tools. IIR separates these concerns.

### Deterministic merge results

`imports` can merge packs, constraints, permissions, tests, and human gates. IIR captures the resolved result after import expansion and merge rules have been applied.

### Permission and risk analysis

Risk analysis should operate on normalized semantics, not on scattered raw YAML fields. IIR is where GovernSpec records derived signals such as external network usage, filesystem write access, confidential inputs, and high-risk tool usage.

### Constraint-preserving compilation

Not every target can express every contract requirement. IIR gives target compilers a common source form so they can emit `constraint_loss` when a downstream surface cannot faithfully preserve a requirement.

## Current IIR shape in v0.1

The current `NormalizedIntent` model includes at least these fields:

- `source_path`
- `metadata`
- `normalized_goal`
- `resolved_context`
- `resolved_inputs`
- `resolved_permissions`
- `merged_constraints`
- `evidence_policy`
- `output_contract`
- `human_gates`
- `test_contract`
- `risk_signals`
- `target_capability_notes`

## Risk signals

v0.1 derives a small deterministic set of static risk signals:

- `external_network`
- `filesystem_write`
- `confidential_input`
- `sensitive_tool`
- `strict_json_output`
- `human_gate_required`

These are not runtime observations. They are static compiler outputs derived from the resolved contract.

## Target capability notes

Target compilers use capability notes to explain what cannot be fully encoded downstream. In v0.1, this is most visible in `mcp-plan`, which emits `constraint_loss` for unsupported guarantees such as:

- per-claim evidence requirements
- stylistic and tone requirements
- post-generation test assertions
- per-section structure constraints

## CLI surface

Use `governspec inspect` to view the normalized IIR:

```bash
governspec inspect examples/customer_brief.govern.yaml
governspec inspect examples/report_json.govern.yaml --format json
```

This is the recommended debugging and review surface when validating import resolution, permission tightening, and target capability behavior.

## Future direction

The current IIR is intentionally compact. Future work may add:

- richer capability graphs
- import trace metadata
- stronger constraint preservation proofs
- workflow-level contract composition
- provider-specific lowering diagnostics
