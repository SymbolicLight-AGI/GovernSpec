from __future__ import annotations

from pathlib import Path

import pytest
from intentspec_core.common.errors import (
    IntentSpecFileError,
    IntentSpecParseError,
    IntentSpecValidationError,
)
from intentspec_core.spec.models import IntentPack, IntentSpec
from intentspec_core.spec.parser import load_document, load_spec

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def test_loads_customer_brief_example() -> None:
    spec = load_spec(EXAMPLES / "customer_brief.intent.yaml")
    assert isinstance(spec, IntentSpec)
    assert spec.metadata.name == "customer_brief"
    assert spec.version == "0.1"


def test_loads_pack_example() -> None:
    document = load_document(EXAMPLES / "packs" / "privacy.intent.yaml")
    assert isinstance(document, IntentPack)
    assert document.kind == "IntentPack"


def test_missing_file_raises_file_error() -> None:
    with pytest.raises(IntentSpecFileError):
        load_spec(EXAMPLES / "missing.intent.yaml")


def test_invalid_yaml_raises_parse_error(tmp_path: Path) -> None:
    broken_file = tmp_path / "broken.intent.yaml"
    broken_file.write_text("version: '0.1'\nkind: [\n", encoding="utf-8")

    with pytest.raises(IntentSpecParseError) as exc_info:
        load_spec(broken_file)
    assert "line " in str(exc_info.value)
    assert exc_info.value.suggestion is not None


def test_missing_goal_raises_validation_error() -> None:
    with pytest.raises(IntentSpecValidationError) as exc_info:
        load_spec(EXAMPLES / "invalid_missing_goal.intent.yaml")
    assert exc_info.value.suggestion is not None
