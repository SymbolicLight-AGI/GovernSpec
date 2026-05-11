from __future__ import annotations

import copy
from pathlib import Path

from governspec_core.imports.resolver import resolve_imports
from governspec_core.spec.models import GovernSpec
from governspec_core.spec.parser import load_spec
from governspec_core.validator import validate_spec

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def _customer_spec() -> GovernSpec:
    return resolve_imports(load_spec(EXAMPLES / "customer_brief.govern.yaml"))


def test_customer_brief_passes_validation() -> None:
    report = validate_spec(_customer_spec())
    assert report.ok is True
    assert report.errors == []


def test_high_risk_tool_without_gate_produces_error() -> None:
    report = validate_spec(load_spec(EXAMPLES / "invalid_dangerous_permission.govern.yaml"))
    assert report.ok is False
    assert any("High-risk tool permissions" in item for item in report.errors)


def test_imported_customer_brief_warns_about_missing_input_path() -> None:
    report = validate_spec(
        resolve_imports(load_spec(EXAMPLES / "imported_customer_brief.govern.yaml"))
    )
    assert any("Required input path" in item for item in report.warnings)


def test_network_without_external_gate_produces_warning() -> None:
    payload = copy.deepcopy(_customer_spec().model_dump(by_alias=True))
    payload["permissions"]["web"] = True
    payload["human_gates"] = []
    spec = GovernSpec.model_validate(payload)
    report = validate_spec(spec)
    assert any("permissions.web or permissions.network" in item for item in report.warnings)


def test_json_output_without_json_schema_assertion_warns() -> None:
    payload = copy.deepcopy(
        load_spec(EXAMPLES / "report_json.govern.yaml").model_dump(by_alias=True)
    )
    payload["tests"] = []
    spec = GovernSpec.model_validate(payload)
    report = validate_spec(spec)
    assert any("json_schema assertion" in item for item in report.warnings)
