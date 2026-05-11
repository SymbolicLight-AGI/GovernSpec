"""Run deterministic offline assertion evaluation for paper samples."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from governspec_core.testing.tester import test_output
from paper_helpers import (
    BENCHMARK_ROOT,
    RESULTS_DIR,
    load_resolved_spec,
    output_sample_labels,
    percent,
    write_json,
)


def run(
    *,
    benchmark_root: Path = BENCHMARK_ROOT,
    results_dir: Path = RESULTS_DIR,
) -> dict[str, Any]:
    labels = output_sample_labels(benchmark_root)
    records: list[dict[str, Any]] = []
    for item in labels:
        spec = load_resolved_spec(
            benchmark_root / "contracts" / f"{item['contract']}.govern.yaml"
        )
        output_text = (benchmark_root / item["output_path"]).read_text(encoding="utf-8")
        report = test_output(spec, output_text)
        records.append(
            {
                "contract": item["contract"],
                "sample": item["sample"],
                "expected_ok": item["expected_ok"],
                "actual_ok": report.ok,
                "targeted_assertion": item["targeted_assertion"],
                "passed": list(report.passed),
                "failed": list(report.failed),
                "included_in_isolated_summary": item["included_in_isolated_summary"],
                "expectation_match": report.ok == item["expected_ok"],
            }
        )

    valid_records = [record for record in records if record["expected_ok"]]
    isolated_defects = [
        record
        for record in records
        if not record["expected_ok"] and record["included_in_isolated_summary"]
    ]
    valid_passed = sum(1 for record in valid_records if record["actual_ok"])
    defects_caught = sum(1 for record in isolated_defects if not record["actual_ok"])
    per_assertion = _per_assertion_summary(isolated_defects)
    payload = {
        "samples": records,
        "summary": {
            "total_samples": len(records),
            "valid_total": len(valid_records),
            "valid_passed": valid_passed,
            "valid_pass_rate": percent(valid_passed, len(valid_records)),
            "isolated_defect_total": len(isolated_defects),
            "isolated_defects_caught": defects_caught,
            "targeted_defect_catch_rate": percent(defects_caught, len(isolated_defects)),
            "per_assertion": per_assertion,
        },
    }
    write_json(results_dir / "assertion_eval.json", payload)
    return payload


def _per_assertion_summary(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    summary: dict[str, dict[str, Any]] = {}
    for record in records:
        assertion_type = record["targeted_assertion"]
        bucket = summary.setdefault(assertion_type, {"total": 0, "caught": 0, "catch_rate": 0.0})
        bucket["total"] += 1
        if not record["actual_ok"]:
            bucket["caught"] += 1
    for bucket in summary.values():
        bucket["catch_rate"] = percent(bucket["caught"], bucket["total"])
    return dict(sorted(summary.items()))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark-root", type=Path, default=BENCHMARK_ROOT)
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    args = parser.parse_args()
    payload = run(benchmark_root=args.benchmark_root, results_dir=args.results_dir)
    summary = payload["summary"]
    print(
        "Assertion eval: "
        f"{summary['valid_passed']}/{summary['valid_total']} valid outputs passed; "
        f"{summary['isolated_defects_caught']}/{summary['isolated_defect_total']} defects caught."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
