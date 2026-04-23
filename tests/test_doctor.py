from __future__ import annotations

from pathlib import Path

import intentspec_core.doctor as doctor


def test_run_doctor_fails_for_unsupported_python(monkeypatch) -> None:
    monkeypatch.setattr(doctor.sys, "version_info", (3, 10, 12))
    report = doctor.run_doctor(Path.cwd())
    assert report.ok is False
    python_check = next(check for check in report.checks if check.name == "python_version")
    assert python_check.status == "error"
    assert "requires Python >= 3.11" in python_check.message
