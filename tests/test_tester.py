from __future__ import annotations

import copy
from pathlib import Path

from intentspec_core.common.utils import read_text
from intentspec_core.imports.resolver import resolve_imports
from intentspec_core.spec.models import IntentSpec
from intentspec_core.spec.parser import load_spec
from intentspec_core.testing import tester as tester_module
from intentspec_core.testing.tester import test_output

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def _customer_spec() -> IntentSpec:
    return resolve_imports(load_spec(EXAMPLES / "customer_brief.intent.yaml"))


def test_customer_brief_output_passes() -> None:
    report = test_output(_customer_spec(), read_text(EXAMPLES / "customer_brief.output.md"))
    assert report.ok is True


def test_report_json_output_passes() -> None:
    spec = load_spec(EXAMPLES / "report_json.intent.yaml")
    report = test_output(spec, read_text(EXAMPLES / "report_json.output.json"))
    assert report.ok is True


def test_json_path_exists_failure_is_reported() -> None:
    spec = load_spec(EXAMPLES / "report_json.intent.yaml")
    broken_output = '{"risks": ["x"], "recommendations": ["a", "b"]}'
    report = test_output(spec, broken_output)
    assert report.ok is False
    assert any("JSON path not found" in item for item in report.failed)


def test_json_array_min_items_failure_is_reported() -> None:
    spec = load_spec(EXAMPLES / "report_json.intent.yaml")
    broken_output = '{"verdict": "x", "risks": ["y"], "recommendations": ["a"]}'
    report = test_output(spec, broken_output)
    assert report.ok is False
    assert any("below minimum" in item for item in report.failed)


def test_invalid_json_fails_fast() -> None:
    spec = load_spec(EXAMPLES / "report_json.intent.yaml")
    report = test_output(spec, "{")
    assert report.ok is False
    assert any("Invalid JSON" in item for item in report.failed)


def test_imported_customer_brief_output_passes() -> None:
    spec = resolve_imports(load_spec(EXAMPLES / "imported_customer_brief.intent.yaml"))
    report = test_output(spec, read_text(EXAMPLES / "imported_customer_brief.output.md"))
    assert report.ok is True


def test_unknown_assertion_type_fails() -> None:
    payload = copy.deepcopy(_customer_spec().model_dump(by_alias=True))
    payload["tests"] = [{"name": "Unknown", "assert": [{"type": "mystery"}]}]
    spec = IntentSpec.model_validate(payload)
    report = test_output(spec, read_text(EXAMPLES / "customer_brief.output.md"))
    assert report.ok is False
    assert any("Unknown assertion type" in item for item in report.failed)


def test_regex_assertion_passes_for_safe_pattern() -> None:
    payload = copy.deepcopy(_customer_spec().model_dump(by_alias=True))
    payload["tests"] = [
        {
            "name": "Regex check",
            "assert": [{"type": "regex", "pattern": r"(?m)^## 一句话结论$"}],
        }
    ]
    spec = IntentSpec.model_validate(payload)
    report = test_output(spec, read_text(EXAMPLES / "customer_brief.output.md"))
    assert report.ok is True


def test_regex_assertion_timeout_is_reported(monkeypatch) -> None:
    payload = copy.deepcopy(_customer_spec().model_dump(by_alias=True))
    payload["tests"] = [
        {
            "name": "Regex timeout",
            "assert": [{"type": "regex", "pattern": r"(a+)+$"}],
        }
    ]
    spec = IntentSpec.model_validate(payload)

    monkeypatch.setattr(
        tester_module,
        "_run_regex_match",
        lambda pattern, output_text: (False, "Regex evaluation timed out after 2 seconds."),
    )

    report = test_output(spec, "a" * 1000)
    assert report.ok is False
    assert any("timed out" in item for item in report.failed)
