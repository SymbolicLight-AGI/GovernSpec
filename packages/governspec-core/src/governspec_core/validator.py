"""Semantic validation for GovernSpec v0.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from governspec_core.common.utils import resolve_path
from governspec_core.spec.models import GovernDocument, GovernPack, GovernSpec


@dataclass(slots=True)
class ValidationReport:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_text(self) -> str:
        lines = [f"Validation status: {'ok' if self.ok else 'failed'}"]
        lines.append("Errors:" if self.errors else "Errors: none")
        if self.errors:
            lines.extend(f"- {message}" for message in self.errors)
        lines.append("Warnings:" if self.warnings else "Warnings: none")
        if self.warnings:
            lines.extend(f"- {message}" for message in self.warnings)
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return asdict(self)


def validate_spec(spec: GovernSpec) -> ValidationReport:
    return _validate_spec(spec)


def validate_document(document: GovernDocument) -> ValidationReport:
    if isinstance(document, GovernSpec):
        return _validate_spec(document)
    return _validate_pack(document)


def _validate_spec(spec: GovernSpec) -> ValidationReport:
    errors: list[str] = []
    warnings: list[str] = []

    high_risk_gate_keywords = (
        "email",
        "邮件",
        "gmail",
        "calendar",
        "delete",
        "purchase",
    )
    if _uses_high_risk_tool(spec) and not _has_confirmation_gate(
        spec, high_risk_gate_keywords
    ):
        errors.append(
            "High-risk tool permissions are enabled, but no matching "
            "ask_confirmation human gate was found."
        )

    if _uses_external_network(spec) and not _has_confirmation_gate(
        spec,
        ("外部网络", "网络", "network", "web", "internet"),
    ):
        warnings.append(
            "permissions.web or permissions.network is enabled without a matching "
            "ask_confirmation human gate."
        )

    if (
        spec.evidence.require_sources
        and spec.output.format != "json"
        and not _has_evidence_section(spec)
    ):
        warnings.append(
            "evidence.require_sources is true, but output.sections does not mention "
            "evidence, sources, or references."
        )

    if not spec.constraints:
        warnings.append("constraints is empty. Consider adding behavioral and safety boundaries.")

    if not spec.tests:
        warnings.append("tests is empty. Consider adding output acceptance checks.")

    if getattr(spec.output, "max_words", 0) and getattr(spec.output, "max_words", 0) < 100:
        warnings.append("output.max_words is below 100 and may be too restrictive.")

    for input_spec in spec.inputs:
        if input_spec.required:
            resolved = resolve_path(spec._source_path, input_spec.path)
            if not resolved.exists():
                warnings.append(f"Required input path does not exist yet: {input_spec.path}")

    if _has_confidential_inputs(spec) and not _mentions_privacy_constraints(spec):
        warnings.append(
            "Confidential inputs are present, but constraints do not mention privacy, "
            "masking, or PII handling."
        )

    if spec.output.format == "json" and spec.output.json_schema and not any(
        assertion.type == "json_schema"
        for test_case in spec.tests
        for assertion in test_case.assertions
    ):
        warnings.append(
            "output.format=json is defined, but tests do not include a json_schema assertion."
        )

    return ValidationReport(ok=not errors, errors=errors, warnings=warnings)


def _validate_pack(pack: GovernPack) -> ValidationReport:
    errors: list[str] = []
    warnings: list[str] = []

    permissions = pack.permissions
    if permissions is not None:
        if _uses_high_risk_tools_from_permissions(permissions) and not _has_confirmation_gate(
            pack, ("email", "邮件", "gmail", "calendar", "delete", "purchase")
        ):
            errors.append(
                "High-risk tool permissions are enabled, but no matching "
                "ask_confirmation human gate was found."
            )
        if _uses_external_network_from_permissions(permissions) and not _has_confirmation_gate(
            pack,
            ("外部网络", "网络", "network", "web", "internet"),
        ):
            warnings.append(
                "permissions.web or permissions.network is enabled without a matching "
                "ask_confirmation human gate."
            )

    if not any(
        [
            permissions is not None,
            bool(pack.constraints),
            bool(pack.evidence),
            bool(pack.quality),
            bool(pack.human_gates),
            bool(pack.tests),
        ]
    ):
        warnings.append(
            "GovernPack does not define reusable governance fields yet."
        )

    return ValidationReport(ok=not errors, errors=errors, warnings=warnings)


def _has_confirmation_gate(document: GovernSpec | GovernPack, keywords: tuple[str, ...]) -> bool:
    lowered_keywords = tuple(keyword.lower() for keyword in keywords)
    for gate in document.human_gates:
        when_text = gate.when.lower()
        if gate.action == "ask_confirmation" and any(
            keyword in when_text for keyword in lowered_keywords
        ):
            return True
    return False


def _uses_external_network(spec: GovernSpec) -> bool:
    return _uses_external_network_from_permissions(spec.permissions)


def _uses_high_risk_tool(spec: GovernSpec) -> bool:
    return _uses_high_risk_tools_from_permissions(spec.permissions)


def _uses_external_network_from_permissions(permissions: object) -> bool:
    return bool(getattr(permissions, "web", False) or getattr(permissions, "network", False))


def _uses_high_risk_tools_from_permissions(permissions: object) -> bool:
    tools = getattr(permissions, "tools", None)
    if tools is None:
        return False
    return any(
        [
            tools.send_email,
            tools.delete_file,
            tools.purchase,
            tools.read_gmail,
            tools.read_calendar,
        ]
    )


def _has_evidence_section(spec: GovernSpec) -> bool:
    evidence_keywords = ("依据", "来源", "证据", "source", "sources", "evidence")
    for section in getattr(spec.output, "sections", []):
        lowered = section.lower()
        if any(keyword in lowered for keyword in evidence_keywords):
            return True
    return False


def _has_confidential_inputs(spec: GovernSpec) -> bool:
    return any(item.privacy.lower() == "confidential" for item in spec.inputs)


def _mentions_privacy_constraints(spec: GovernSpec) -> bool:
    joined_constraints = " ".join(spec.constraints).lower()
    privacy_keywords = (
        "隐私",
        "脱敏",
        "pii",
        "手机号",
        "邮箱",
        "privacy",
        "email",
        "phone",
        "sensitive",
        "personal data",
    )
    return any(keyword in joined_constraints for keyword in privacy_keywords)
