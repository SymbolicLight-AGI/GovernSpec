from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_benchmark_runner_succeeds() -> None:
    result = subprocess.run(
        ["python", "benchmark/run_benchmark.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "Pass rate" in result.stdout
