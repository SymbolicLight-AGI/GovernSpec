"""Run all GovernSpec reproducibility benchmark experiments."""

from __future__ import annotations

import argparse
from pathlib import Path

from benchmark_helpers import BENCHMARK_ROOT, RESULTS_DIR
from render_tables import run as render_tables
from run_annotation_agreement import run as run_annotation_agreement
from run_assertion_eval import run as run_assertion_eval
from run_compile_matrix import run as run_compile_matrix
from run_roundtrip import run as run_roundtrip


def run_all(
    *,
    benchmark_root: Path = BENCHMARK_ROOT,
    results_dir: Path = RESULTS_DIR,
) -> None:
    results_dir.mkdir(parents=True, exist_ok=True)
    run_compile_matrix(benchmark_root=benchmark_root, results_dir=results_dir)
    run_roundtrip(benchmark_root=benchmark_root, results_dir=results_dir)
    run_assertion_eval(benchmark_root=benchmark_root, results_dir=results_dir)
    run_annotation_agreement(benchmark_root=benchmark_root, results_dir=results_dir)
    render_tables(results_dir=results_dir)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark-root", type=Path, default=BENCHMARK_ROOT)
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    args = parser.parse_args()
    run_all(benchmark_root=args.benchmark_root, results_dir=args.results_dir)
    print(f"GovernSpec reproducibility benchmark results written to {args.results_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



