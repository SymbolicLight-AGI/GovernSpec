"""Run the ICSE paper compile matrix experiment."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from intentspec_core.common.errors import IntentSpecError
from intentspec_core.iir.builder import build_iir
from intentspec_core.targets.compiler import compile_target
from paper_helpers import (
    BENCHMARK_ROOT,
    REPRESENTATIVE_TARGETS,
    RESULTS_DIR,
    artifact_text,
    contract_name,
    contract_paths,
    load_resolved_spec,
    percent,
    write_json,
)


def run(
    *,
    benchmark_root: Path = BENCHMARK_ROOT,
    results_dir: Path = RESULTS_DIR,
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for contract_path in contract_paths(benchmark_root):
        spec = load_resolved_spec(contract_path)
        iir = build_iir(spec)
        for target in REPRESENTATIVE_TARGETS:
            capability_notes = iir.target_capability_notes.get(target, [])
            record = {
                "contract": contract_name(contract_path),
                "target": target,
                "ok": False,
                "artifact_kind": None,
                "error_type": None,
                "error_message": None,
                "capability_notes_count": len(capability_notes),
            }
            try:
                artifact = compile_target(spec, target)
                artifact_text(artifact, target)
                record.update({"ok": True, "artifact_kind": artifact.kind})
            except IntentSpecError as exc:
                record.update(
                    {
                        "error_type": exc.__class__.__name__,
                        "error_message": str(exc),
                    }
                )
            except Exception as exc:  # pragma: no cover - defensive experiment reporting
                record.update(
                    {
                        "error_type": exc.__class__.__name__,
                        "error_message": str(exc),
                    }
                )
            records.append(record)

    ok_count = sum(1 for record in records if record["ok"])
    payload = {
        "contracts": [contract_name(path) for path in contract_paths(benchmark_root)],
        "targets": REPRESENTATIVE_TARGETS,
        "results": records,
        "summary": {
            "contract_count": len(contract_paths(benchmark_root)),
            "target_count": len(REPRESENTATIVE_TARGETS),
            "total": len(records),
            "ok": ok_count,
            "failed": len(records) - ok_count,
            "compile_success_rate": percent(ok_count, len(records)),
        },
    }
    write_json(results_dir / "compile_matrix.json", payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark-root", type=Path, default=BENCHMARK_ROOT)
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    args = parser.parse_args()
    payload = run(benchmark_root=args.benchmark_root, results_dir=args.results_dir)
    summary = payload["summary"]
    print(
        "Compile matrix: "
        f"{summary['ok']}/{summary['total']} succeeded "
        f"({summary['compile_success_rate']}%)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
