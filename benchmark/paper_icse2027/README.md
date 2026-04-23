# ICSE 2027 paper benchmark

This directory contains the local, reproducible artifact-level benchmark used by the
ICSE demo paper draft.

Run all experiments from the repository root:

```bash
python benchmark/paper_icse2027/scripts/run_all.py
```

The benchmark intentionally avoids external agent execution. It measures compilation,
round-trip import fidelity, and deterministic offline assertion behavior using the
current IntentSpec implementation.
