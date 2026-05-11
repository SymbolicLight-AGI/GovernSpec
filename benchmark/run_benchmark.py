"""Run offline benchmark checks against stored outputs."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

from governspec_core.common.errors import GovernSpecError
from governspec_core.imports.resolver import resolve_imports
from governspec_core.spec.parser import load_spec
from governspec_core.targets.compiler import compile_target
from governspec_core.testing.tester import test_output

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TASKS_DIR = ROOT / "benchmark" / "tasks"
DEFAULT_OUTPUTS_DIR = ROOT / "benchmark" / "outputs"


@dataclass(slots=True)
class BenchmarkResult:
    name: str
    ok: bool
    failed: list[str]
    warnings: list[str]
    constraint_loss: list[str] = field(default_factory=list)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run offline GovernSpec benchmarks.")
    parser.add_argument("--tasks-dir", type=Path, default=DEFAULT_TASKS_DIR)
    parser.add_argument("--outputs-dir", type=Path, default=DEFAULT_OUTPUTS_DIR)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()

    results = run_benchmark(args.tasks_dir, args.outputs_dir)
    passed = sum(1 for result in results if result.ok)
    total = len(results)
    failed = total - passed
    pass_rate = (passed / total * 100) if total else 0.0
    constraint_loss_count = sum(len(result.constraint_loss) for result in results)
    payload = {
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": round(pass_rate, 2),
        "constraint_loss_count": constraint_loss_count,
        "results": [asdict(result) for result in results],
    }

    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("Benchmark summary")
        print(f"Total tasks: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Pass rate: {payload['pass_rate']}%")
        print(f"Constraint loss count: {constraint_loss_count}")
        for result in results:
            status = "ok" if result.ok else "failed"
            print(f"- {result.name}: {status}")
            for item in result.failed:
                print(f"  failure: {item}")
            for item in result.constraint_loss:
                print(f"  constraint_loss: {item}")

    return 0 if failed == 0 else 1


def run_benchmark(tasks_dir: Path, outputs_dir: Path) -> list[BenchmarkResult]:
    results: list[BenchmarkResult] = []
    for task_file in sorted(tasks_dir.glob("*.govern.yaml")):
        output_stem = task_file.name.replace(".govern.yaml", ".output")
        output_file = _resolve_output_file(outputs_dir, output_stem)
        if not output_file.exists():
            results.append(
                BenchmarkResult(
                    name=task_file.name.removesuffix(".govern.yaml"),
                    ok=False,
                    failed=[f"Missing output file for task: {task_file.name}"],
                    warnings=[],
                )
            )
            continue
        try:
            spec = resolve_imports(load_spec(task_file))
            output_text = output_file.read_text(encoding="utf-8")
            report = test_output(spec, output_text)
            mcp_plan = json.loads(compile_target(spec, "mcp-plan").content or "{}")
            constraint_loss = list(mcp_plan.get("constraint_loss", []))
            results.append(
                BenchmarkResult(
                    name=task_file.name.removesuffix(".govern.yaml"),
                    ok=report.ok,
                    failed=report.failed,
                    warnings=report.warnings,
                    constraint_loss=constraint_loss,
                )
            )
        except GovernSpecError as exc:
            results.append(
                BenchmarkResult(
                    name=task_file.name.removesuffix(".govern.yaml"),
                    ok=False,
                    failed=[str(exc)],
                    warnings=[],
                )
            )
    return results


def _resolve_output_file(outputs_dir: Path, output_stem: str) -> Path:
    for extension in (".md", ".json"):
        candidate = outputs_dir / f"{output_stem}{extension}"
        if candidate.exists():
            return candidate
    return outputs_dir / f"{output_stem}.md"


if __name__ == "__main__":
    sys.exit(main())
