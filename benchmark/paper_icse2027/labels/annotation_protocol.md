# Annotation protocol for the paper benchmark

This protocol records the local annotation procedure used for the larger
artifact-level benchmark. It does not represent independent human-subject data and
does not call external model APIs.

## Units

Each annotation unit is one output sample listed in `output_samples*.json`.

## Annotators

The current release uses two Codex-assisted annotation passes:

- `codex_pass_a`: first-pass label assignment from the sample and contract.
- `codex_pass_b`: second-pass consistency label assignment from the same materials.

The labels are suitable for reporting an assisted pilot consistency check. They must
not be described as independent human-human agreement.

## Fields

- `expected_ok`: whether the output should pass the contract tests.
- `targeted_assertion`: the primary assertion type targeted by a defect sample, or
  `none` for valid samples.
- `failure_scope`: `none` for valid samples, `isolated` when the sample is intended
  to target one assertion family, and `coupled` when several assertion families are
  intentionally entangled.
- `output_format`: `markdown` or `json`.

## Adjudication

The `adjudicated` label is the gold label used for dataset consistency checks and
paper reporting. Disagreements between the two Codex-assisted passes are resolved by
checking the contract tests and the output sample directly.

