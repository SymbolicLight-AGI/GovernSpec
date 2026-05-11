from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

from governspec_core.imports.resolver import resolve_imports
from governspec_core.spec.models import GovernSpec
from governspec_core.spec.parser import load_spec

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "benchmark" / "paper_icse2027"
SCRIPTS = BENCHMARK / "scripts"


def _load_helpers():
    module_path = SCRIPTS / "paper_helpers.py"
    spec = importlib.util.spec_from_file_location("paper_helpers_for_tests", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


HELPERS = _load_helpers()


def test_paper_dataset_is_consistent() -> None:
    contracts = sorted((BENCHMARK / "contracts").glob("*.govern.yaml"))
    output_labels = HELPERS.output_sample_labels(BENCHMARK)
    handwritten_labels = HELPERS.handwritten_artifact_labels(BENCHMARK)
    assertion_types = {
        label["targeted_assertion"]
        for label in output_labels
        if label["targeted_assertion"] is not None
    }

    assert len(contracts) == 20
    assert len(output_labels) == 52
    assert len(handwritten_labels) == 20
    assert assertion_types == {
        "contains",
        "json_array_min_items",
        "json_path_exists",
        "json_schema",
        "max_chars",
        "max_words",
        "no_regex",
        "not_contains",
        "regex",
        "required_sections",
    }

    contract_names = {path.name.removesuffix(".govern.yaml") for path in contracts}
    valid_contracts = {
        label["contract"] for label in output_labels if label["expected_ok"] is True
    }
    assert valid_contracts == contract_names
    for label in output_labels:
        assert (BENCHMARK / label["output_path"]).is_file()
    for label in handwritten_labels:
        assert (BENCHMARK / label["artifact"]).is_file()


def test_compile_matrix_runner_smoke(tmp_path: Path) -> None:
    out_dir = tmp_path / "results"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "run_compile_matrix.py"),
            "--results-dir",
            str(out_dir),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads((out_dir / "compile_matrix.json").read_text(encoding="utf-8"))
    assert {"contracts", "targets", "results", "summary"} <= set(payload)


def test_roundtrip_runner_smoke(tmp_path: Path) -> None:
    out_dir = tmp_path / "results"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "run_roundtrip.py"),
            "--results-dir",
            str(out_dir),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads((out_dir / "roundtrip_fidelity.json").read_text(encoding="utf-8"))
    assert {"compiled", "handwritten", "summary"} <= set(payload)


def test_assertion_eval_runner_smoke(tmp_path: Path) -> None:
    out_dir = tmp_path / "results"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "run_assertion_eval.py"),
            "--results-dir",
            str(out_dir),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads((out_dir / "assertion_eval.json").read_text(encoding="utf-8"))
    assert {"samples", "summary"} <= set(payload)


def test_run_all_generates_paper_outputs(tmp_path: Path) -> None:
    out_dir = tmp_path / "results"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "run_all.py"),
            "--results-dir",
            str(out_dir),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    for name in [
        "compile_matrix.json",
        "roundtrip_fidelity.json",
        "assertion_eval.json",
        "summary.json",
        "tables.md",
        "numbers.md",
    ]:
        assert (out_dir / name).is_file()


def test_fidelity_comparator_exact_match() -> None:
    spec = resolve_imports(load_spec(BENCHMARK / "contracts" / "report_json.govern.yaml"))
    comparison = HELPERS.compare_core_fields(spec, spec)
    assert all(comparison["field_matches"].values())
    assert comparison["exact_match_ratio"] == 1.0


def test_fidelity_comparator_detects_list_order_mismatch() -> None:
    spec = resolve_imports(load_spec(BENCHMARK / "contracts" / "code_review.govern.yaml"))
    payload = copy.deepcopy(spec.model_dump(by_alias=True))
    payload["constraints"] = list(reversed(payload["constraints"]))
    actual = GovernSpec.model_validate(payload)

    comparison = HELPERS.compare_core_fields(spec, actual)

    assert comparison["field_matches"]["constraints"] is False
    assert comparison["exact_match_ratio"] < 1.0


def test_fidelity_comparator_detects_schema_only_mismatch() -> None:
    spec = resolve_imports(load_spec(BENCHMARK / "contracts" / "report_json.govern.yaml"))
    payload = copy.deepcopy(spec.model_dump(by_alias=True))
    payload["output"]["schema"]["required"] = ["verdict"]
    actual = GovernSpec.model_validate(payload)

    comparison = HELPERS.compare_core_fields(spec, actual)

    assert comparison["field_matches"]["output"] is False
    assert comparison["field_matches"]["goal"] is True


def test_fidelity_comparator_handles_resolved_imports() -> None:
    spec = resolve_imports(
        load_spec(BENCHMARK / "contracts" / "imported_customer_brief.govern.yaml")
    )
    actual = GovernSpec.model_validate(spec.model_dump(by_alias=True))

    comparison = HELPERS.compare_core_fields(spec, actual)

    assert all(comparison["field_matches"].values())
