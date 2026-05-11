# ICSE 2027 paper benchmark

This directory contains the local, reproducible artifact-level benchmark used by the
GovernSpec paper drafts. It includes the original ICSE demo seed set plus an
expanded local dataset for stronger artifact-level evidence.

Run all experiments from the repository root:

```bash
python benchmark/paper_icse2027/scripts/run_all.py
```

The benchmark intentionally avoids external agent execution. It measures compilation,
round-trip import fidelity, deterministic offline assertion behavior, and assisted
annotation agreement using the current GovernSpec implementation.

Current dataset size:

- 20 contracts
- 52 output samples, including 20 valid outputs and 32 targeted defects
- 20 handwritten artifacts
- 29 output samples with two Codex-assisted annotation passes for agreement analysis

The annotation agreement labels are a pilot consistency artifact. They should not be
reported as independent human-human agreement.
