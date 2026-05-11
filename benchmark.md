# Benchmark Template

Use this file to document repeatable GovernSpec v0.1 benchmark runs.

## Goal

State the benchmark question clearly.

Examples:

- Does GovernSpec improve strict JSON contract compliance over a plain prompt baseline?
- Do imported packs improve privacy and no-network consistency across tasks?
- Does `constraint_loss` reveal target limitations early enough to change compiler choices?

## Scope

- Version under test:
- Date:
- Owner:
- Environment:
  - Python:
  - OS:
  - Tool version:
- Runtime:
  - If no model is involved, write `offline artifact replay`

## Dataset

| Task ID | Task Type | Intent File | Output File | Notes |
| --- | --- | --- | --- | --- |
| T-001 | markdown | `benchmark/tasks/customer_brief.govern.yaml` | `benchmark/outputs/customer_brief.output.md` | |
| T-002 | json | `benchmark/tasks/report_json.govern.yaml` | `benchmark/outputs/report_json.output.json` | |
| T-003 | imports | `benchmark/tasks/imported_customer_brief.govern.yaml` | `benchmark/outputs/imported_customer_brief.output.md` | |

## Variants

Describe each benchmark group.

### Group A

- Name:
- Description:
- Prompt or contract source:
- Output source:

### Group B

- Name:
- Description:
- Prompt or contract source:
- Output source:

## Metrics

| Metric | Definition | Measurement Method |
| --- | --- | --- |
| Test pass rate | Share of runs that pass `governspec test` | CLI |
| JSON schema pass rate | Share of JSON outputs that satisfy `output.schema` | `json_schema` |
| Import consistency | Shared constraints preserved after `imports` | `governspec inspect` + tests |
| Privacy leakage rate | Forbidden PII patterns appear in output | `no_regex` |
| Constraint loss count | Number of lossy target notes emitted | benchmark runner + `mcp-plan.constraint_loss` |

## Commands

```bash
python benchmark/run_benchmark.py
python benchmark/reproducibility/scripts/run_all.py
governspec inspect benchmark/tasks/imported_customer_brief.govern.yaml --format json
governspec compile benchmark/tasks/report_json.govern.yaml --target openai-structured
governspec compile benchmark/tasks/report_json.govern.yaml --target mcp-plan
```

## Results Summary

| Group | Total Runs | Passed | Failed | Pass Rate | Constraint Loss Count | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| A |  |  |  |  |  |  |
| B |  |  |  |  |  |  |

## Constraint Loss Review

### Target

- Target name:
- Observed `constraint_loss` entries:

### Interpretation

- Which requirements could not be preserved:
- Whether the loss is acceptable:

## Per-Task Notes

### T-001

- Outcome:
- Failure mode:
- Notable observations:

## Interpretation

- What improved:
- What did not improve:
- Which targets are still too lossy:
- Where the benchmark remains weak:

## Threats to Validity

- small sample size
- synthetic outputs
- offline replay instead of live model variance
- imported packs may hide authoring complexity

## Next Actions

- add more JSON tasks
- add more pack combinations
- compare `agents-md` and `prompt` usage in real repositories
- add human review counts
