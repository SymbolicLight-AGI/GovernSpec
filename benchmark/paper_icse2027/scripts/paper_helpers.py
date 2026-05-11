"""Shared helpers for the ICSE 2027 paper benchmark."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from governspec_core.imports.resolver import resolve_imports
from governspec_core.spec.models import GovernSpec, JsonOutput
from governspec_core.spec.parser import load_spec
from governspec_core.targets.compiler import CompiledArtifact

BENCHMARK_ROOT = Path(__file__).resolve().parents[1]
CONTRACTS_DIR = BENCHMARK_ROOT / "contracts"
LABELS_DIR = BENCHMARK_ROOT / "labels"
RESULTS_DIR = BENCHMARK_ROOT / "results"

OUTPUT_LABEL_FILES = [
    "output_samples.json",
    "output_samples_extended.json",
]

HANDWRITTEN_LABEL_FILES = [
    "handwritten_artifacts.json",
    "handwritten_artifacts_extended.json",
]

REPRESENTATIVE_TARGETS = [
    "agents-md",
    "claude-md",
    "cursor-rules",
    "openai-structured",
    "gemini-structured",
    "mcp-plan",
]

IMPORTABLE_TARGETS = [
    "agents-md",
    "claude-md",
    "cursor-rules",
    "openai-structured",
    "gemini-structured",
]

CORE_FIELDS = [
    "goal",
    "permissions",
    "constraints",
    "human_gates",
    "output",
    "tests",
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_json_arrays(label_dir: Path, filenames: list[str]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for filename in filenames:
        path = label_dir / filename
        if path.is_file():
            items.extend(read_json(path))
    return items


def output_sample_labels(benchmark_root: Path = BENCHMARK_ROOT) -> list[dict[str, Any]]:
    return read_json_arrays(benchmark_root / "labels", OUTPUT_LABEL_FILES)


def handwritten_artifact_labels(benchmark_root: Path = BENCHMARK_ROOT) -> list[dict[str, Any]]:
    return read_json_arrays(benchmark_root / "labels", HANDWRITTEN_LABEL_FILES)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def percent(numerator: int | float, denominator: int | float) -> float:
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100, 2)


def contract_paths(benchmark_root: Path = BENCHMARK_ROOT) -> list[Path]:
    return sorted((benchmark_root / "contracts").glob("*.govern.yaml"))


def contract_name(path: Path) -> str:
    return path.name.removesuffix(".govern.yaml")


def load_resolved_spec(path: Path) -> GovernSpec:
    return resolve_imports(load_spec(path))


def artifact_text(artifact: CompiledArtifact, target: str) -> str:
    if artifact.content is not None:
        return artifact.content
    if target == "cursor-rules":
        return artifact.files[".cursor/rules/governspec.mdc"]
    first_path = sorted(artifact.files)[0]
    return artifact.files[first_path]


def core_fields(spec: GovernSpec) -> dict[str, Any]:
    output = spec.output
    output_payload = output.model_dump(by_alias=True)
    if isinstance(output, JsonOutput):
        output_payload["schema"] = stable_json(output_payload["schema"])
    return {
        "goal": spec.task.goal,
        "permissions": stable_json(spec.permissions.model_dump()),
        "constraints": list(spec.constraints),
        "human_gates": [gate.model_dump() for gate in spec.human_gates],
        "output": stable_json(output_payload),
        "tests": stable_json([test.model_dump(by_alias=True) for test in spec.tests]),
    }


def stable_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: stable_json(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [stable_json(item) for item in value]
    return value


def spec_from_payload(payload: dict[str, Any]) -> GovernSpec:
    return GovernSpec.model_validate(payload)


def compare_core_fields(expected: GovernSpec, actual: GovernSpec) -> dict[str, Any]:
    expected_fields = core_fields(expected)
    actual_fields = core_fields(actual)
    field_matches = {
        field: expected_fields[field] == actual_fields[field] for field in CORE_FIELDS
    }
    matched = sum(1 for value in field_matches.values() if value)
    return {
        "field_matches": field_matches,
        "exact_match_ratio": round(matched / len(CORE_FIELDS), 4),
        "diff_snippet": build_diff_snippet(expected_fields, actual_fields),
    }


def build_diff_snippet(expected: dict[str, Any], actual: dict[str, Any]) -> str:
    diffs: list[str] = []
    for field in CORE_FIELDS:
        if expected[field] == actual[field]:
            continue
        diffs.append(
            f"{field}: expected {short_repr(expected[field])}; "
            f"got {short_repr(actual[field])}"
        )
    return " | ".join(diffs[:3])


def short_repr(value: Any, *, limit: int = 120) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def evaluate_handwritten_expectations(
    payload: dict[str, Any], expected: dict[str, Any]
) -> dict[str, bool]:
    matches: dict[str, bool] = {}
    if "goal_contains" in expected:
        matches["goal_contains"] = expected["goal_contains"].lower() in (
            payload.get("task", {}).get("goal", "").lower()
        )
    if "constraints_contain" in expected:
        constraints = payload.get("constraints", [])
        matches["constraints_contain"] = all(
            item in constraints for item in expected["constraints_contain"]
        )
    if "sections_contain" in expected:
        sections = payload.get("output", {}).get("sections", [])
        matches["sections_contain"] = all(item in sections for item in expected["sections_contain"])
    if "tests_contain" in expected:
        test_names = [item.get("name", "") for item in payload.get("tests", [])]
        matches["tests_contain"] = all(item in test_names for item in expected["tests_contain"])
    if "human_gates_contain" in expected:
        gate_text = " ".join(item.get("when", "") for item in payload.get("human_gates", []))
        matches["human_gates_contain"] = all(
            item in gate_text for item in expected["human_gates_contain"]
        )
    if "json_required_contain" in expected:
        required = payload.get("output", {}).get("schema", {}).get("required", [])
        matches["json_required_contain"] = all(
            item in required for item in expected["json_required_contain"]
        )
    return matches


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)
