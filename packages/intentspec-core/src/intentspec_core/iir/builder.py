"""Build and inspect IntentSpec IIR."""

from __future__ import annotations

from typing import Any

from intentspec_core.iir.models import NormalizedIntent, OutputContract
from intentspec_core.spec.models import IntentDocument, IntentPack, IntentSpec, JsonOutput


def build_iir(spec: IntentSpec) -> NormalizedIntent:
    risk_signals = _collect_risk_signals(spec)
    return NormalizedIntent(
        source_path=str(spec._source_path),
        metadata=spec.metadata.model_dump(),
        normalized_goal=spec.task.goal.strip(),
        resolved_context=spec.context.model_dump(),
        resolved_inputs=[item.model_dump() for item in spec.inputs],
        resolved_permissions=spec.permissions.model_dump(),
        merged_constraints=list(spec.constraints),
        evidence_policy=spec.evidence.model_dump(),
        output_contract=_build_output_contract(spec),
        human_gates=[gate.model_dump() for gate in spec.human_gates],
        test_contract=[item.model_dump(by_alias=True) for item in spec.tests],
        risk_signals=risk_signals,
        target_capability_notes=_build_target_capability_notes(spec),
    )


def inspect_iir(spec: IntentSpec) -> dict[str, Any]:
    return build_iir(spec).model_dump(by_alias=True)


def inspect_document(document: IntentDocument) -> dict[str, Any]:
    if isinstance(document, IntentSpec):
        return inspect_iir(document)
    return _inspect_pack(document)


def _build_output_contract(spec: IntentSpec) -> OutputContract:
    output = spec.output
    if isinstance(output, JsonOutput):
        return OutputContract(
            format=output.format,
            language=output.language,
            schema=output.json_schema,
        )
    return OutputContract(
        format=output.format,
        language=output.language,
        max_words=output.max_words,
        sections=list(output.sections),
    )


def _collect_risk_signals(spec: IntentSpec) -> list[str]:
    signals: list[str] = []
    if spec.permissions.web or spec.permissions.network:
        signals.append("external_network")
    if spec.permissions.filesystem.write or spec.permissions.tools.create_file:
        signals.append("filesystem_write")
    if any(item.privacy.lower() == "confidential" for item in spec.inputs):
        signals.append("confidential_input")
    if any(
        [
            spec.permissions.tools.send_email,
            spec.permissions.tools.delete_file,
            spec.permissions.tools.purchase,
            spec.permissions.tools.read_gmail,
            spec.permissions.tools.read_calendar,
        ]
    ):
        signals.append("sensitive_tool")
    if spec.output.format == "json":
        signals.append("strict_json_output")
    if any(gate.action == "ask_confirmation" for gate in spec.human_gates):
        signals.append("human_gate_required")
    return signals


def _build_target_capability_notes(spec: IntentSpec) -> dict[str, list[str]]:
    notes: dict[str, list[str]] = {
        "agents-md": [],
        "antigravity-rules": [],
        "claude-md": [],
        "cursor-rules": [],
        "mcp-plan": [],
        "skill": [],
    }
    if spec.evidence.require_sources:
        notes["mcp-plan"].append(
            "Target MCP plan cannot fully encode per-claim evidence requirements."
        )
        for target in ("agents-md", "claude-md", "cursor-rules", "antigravity-rules"):
            notes[target].append(
                "Instruction documents can describe evidence rules, but cannot "
                "machine-enforce per-claim evidence."
            )
        notes["skill"].append(
            "SKILL bundles can document evidence rules, but cannot structurally enforce them."
        )
    if spec.quality.tone or spec.quality.must_avoid:
        notes["mcp-plan"].append(
            "Target MCP plan cannot fully encode stylistic or tone requirements."
        )
    if spec.tests:
        notes["mcp-plan"].append(
            "Target MCP plan cannot directly encode post-generation test assertions."
        )
    if getattr(spec.output, "sections", []):
        notes["mcp-plan"].append(
            "Target MCP plan cannot fully encode per-section output structure."
        )
    return {target: values for target, values in notes.items() if values}


def _inspect_pack(pack: IntentPack) -> dict[str, Any]:
    return {
        "source_path": str(pack._source_path),
        "kind": pack.kind,
        "metadata": pack.metadata.model_dump(),
        "imports": list(pack.imports),
        "resolved_imports": [str(path) for path in pack._resolved_imports],
        "resolved_permissions": pack.permissions.model_dump() if pack.permissions else None,
        "merged_constraints": list(pack.constraints),
        "evidence_policy": pack.evidence.model_dump() if pack.evidence else None,
        "quality": pack.quality.model_dump() if pack.quality else None,
        "human_gates": [gate.model_dump() for gate in pack.human_gates],
        "test_contract": [item.model_dump(by_alias=True) for item in pack.tests],
    }
