"""Run compiled and handwritten reverse-import fidelity experiments."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from governspec_core.common.errors import GovernSpecError
from governspec_core.importers.reverse import import_from_artifact, import_from_string
from governspec_core.targets.compiler import compile_target
from paper_helpers import (
    BENCHMARK_ROOT,
    IMPORTABLE_TARGETS,
    RESULTS_DIR,
    artifact_text,
    compare_core_fields,
    contract_name,
    contract_paths,
    evaluate_handwritten_expectations,
    handwritten_artifact_labels,
    load_resolved_spec,
    percent,
    spec_from_payload,
    write_json,
)


def run(
    *,
    benchmark_root: Path = BENCHMARK_ROOT,
    results_dir: Path = RESULTS_DIR,
) -> dict[str, Any]:
    compiled_records = _run_compiled_roundtrip(benchmark_root)
    handwritten_records = _run_handwritten_roundtrip(benchmark_root)
    successful_compiled = [record for record in compiled_records if record["ok"]]
    successful_handwritten = [record for record in handwritten_records if record["ok"]]
    average_compiled_ratio = _average(
        record["exact_match_ratio"] for record in successful_compiled
    )
    average_handwritten_ratio = _average(
        record["exact_match_ratio"] for record in successful_handwritten
    )
    payload = {
        "compiled": compiled_records,
        "handwritten": handwritten_records,
        "summary": {
            "compiled_total": len(compiled_records),
            "compiled_ok": len(successful_compiled),
            "compiled_import_success_rate": percent(
                len(successful_compiled), len(compiled_records)
            ),
            "compiled_average_field_fidelity": round(average_compiled_ratio * 100, 2),
            "handwritten_total": len(handwritten_records),
            "handwritten_ok": len(successful_handwritten),
            "handwritten_import_success_rate": percent(
                len(successful_handwritten), len(handwritten_records)
            ),
            "handwritten_average_gold_match": round(average_handwritten_ratio * 100, 2),
        },
    }
    write_json(results_dir / "roundtrip_fidelity.json", payload)
    return payload


def _run_compiled_roundtrip(benchmark_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for contract_path in contract_paths(benchmark_root):
        spec = load_resolved_spec(contract_path)
        for source_type in IMPORTABLE_TARGETS:
            record = {
                "contract": contract_name(contract_path),
                "source_type": source_type,
                "ok": False,
                "field_matches": {},
                "exact_match_ratio": 0.0,
                "diff_snippet": "",
                "error_type": None,
                "error_message": None,
            }
            try:
                compiled = compile_target(spec, source_type)
                imported = import_from_string(artifact_text(compiled, source_type), source_type)
                recovered = spec_from_payload(imported)
                comparison = compare_core_fields(spec, recovered)
                record.update({"ok": True, **comparison})
            except GovernSpecError as exc:
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
    return records


def _run_handwritten_roundtrip(benchmark_root: Path) -> list[dict[str, Any]]:
    labels = handwritten_artifact_labels(benchmark_root)
    records: list[dict[str, Any]] = []
    for item in labels:
        artifact_path = benchmark_root / item["artifact"]
        source_type = item["source_type"]
        record = {
            "contract": Path(item["artifact"]).stem,
            "source_type": source_type,
            "ok": False,
            "field_matches": {},
            "exact_match_ratio": 0.0,
            "diff_snippet": "",
            "error_type": None,
            "error_message": None,
        }
        try:
            imported = import_from_artifact(artifact_path, source_type=source_type)
            matches = evaluate_handwritten_expectations(imported, item["expected"])
            ratio = _average(1.0 if value else 0.0 for value in matches.values())
            record.update(
                {
                    "ok": True,
                    "field_matches": matches,
                    "exact_match_ratio": round(ratio, 4),
                    "diff_snippet": _handwritten_diff(matches),
                }
            )
        except GovernSpecError as exc:
            record.update(
                {
                    "error_type": exc.__class__.__name__,
                    "error_message": str(exc),
                }
            )
        records.append(record)
    return records


def _average(values: Any) -> float:
    collected = list(values)
    if not collected:
        return 0.0
    return sum(collected) / len(collected)


def _handwritten_diff(matches: dict[str, bool]) -> str:
    missing = [key for key, value in matches.items() if not value]
    if not missing:
        return ""
    return "Missing expected handwritten signals: " + ", ".join(missing)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark-root", type=Path, default=BENCHMARK_ROOT)
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    args = parser.parse_args()
    payload = run(benchmark_root=args.benchmark_root, results_dir=args.results_dir)
    summary = payload["summary"]
    print(
        "Round-trip: "
        f"{summary['compiled_ok']}/{summary['compiled_total']} compiled artifacts imported; "
        f"{summary['handwritten_ok']}/{summary['handwritten_total']} "
        "handwritten artifacts imported."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
