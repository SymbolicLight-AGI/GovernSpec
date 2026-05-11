"""Compile GovernSpec into target artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from governspec_core.common.errors import GovernSpecCompileError
from governspec_core.common.utils import dump_json, render_markdown_list
from governspec_core.iir.builder import build_iir
from governspec_core.iir.models import NormalizedIntent
from governspec_core.spec.models import GovernSpec

SUPPORTED_TARGETS = {
    "agents-md",
    "antigravity-rules",
    "claude-md",
    "cursor-rules",
    "gemini-structured",
    "mcp-plan",
    "openai-json",
    "openai-structured",
    "prompt",
    "skill",
}

_GEMINI_ALLOWED_TYPES = {"object", "array", "string", "integer", "number", "boolean"}
_GEMINI_ALLOWED_SCHEMA_KEYS = {
    "additionalProperties",
    "description",
    "enum",
    "items",
    "maxItems",
    "minItems",
    "properties",
    "required",
    "type",
}


@dataclass(slots=True)
class CompiledArtifact:
    kind: str
    content: str | None = None
    files: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compile_target(spec: GovernSpec, target: str) -> CompiledArtifact:
    return compile_iir(build_iir(spec), target)


def compile_iir(iir: NormalizedIntent, target: str) -> CompiledArtifact:
    normalized_target = target.strip().lower()
    if normalized_target not in SUPPORTED_TARGETS:
        raise GovernSpecCompileError(
            f"Unsupported compile target: {target}",
            suggestion=f"Use one of: {', '.join(sorted(SUPPORTED_TARGETS))}.",
            details={"target": target, "supported_targets": sorted(SUPPORTED_TARGETS)},
        )

    if normalized_target == "prompt":
        return CompiledArtifact(kind="text", content=_compile_prompt(iir))
    if normalized_target == "openai-json":
        return CompiledArtifact(kind="text", content=_compile_openai_json(iir))
    if normalized_target == "openai-structured":
        return CompiledArtifact(kind="text", content=_compile_openai_structured(iir))
    if normalized_target == "gemini-structured":
        return CompiledArtifact(kind="text", content=_compile_gemini_structured(iir))
    if normalized_target == "agents-md":
        return CompiledArtifact(
            kind="text",
            content=_compile_instruction_markdown(iir, "AGENTS.md"),
        )
    if normalized_target == "claude-md":
        return CompiledArtifact(
            kind="text",
            content=_compile_instruction_markdown(iir, "CLAUDE.md"),
        )
    if normalized_target == "cursor-rules":
        return CompiledArtifact(kind="bundle", files=_compile_cursor_rules_bundle(iir))
    if normalized_target == "antigravity-rules":
        return CompiledArtifact(kind="bundle", files=_compile_antigravity_rules_bundle(iir))
    if normalized_target == "skill":
        return CompiledArtifact(kind="bundle", files=_compile_skill_bundle(iir))
    if normalized_target == "mcp-plan":
        return CompiledArtifact(kind="text", content=_compile_mcp_plan(iir))

    raise GovernSpecCompileError(
        f"Unsupported compile target: {target}",
        suggestion=f"Use one of: {', '.join(sorted(SUPPORTED_TARGETS))}.",
        details={"target": target, "supported_targets": sorted(SUPPORTED_TARGETS)},
    )


def _compile_prompt(iir: NormalizedIntent) -> str:
    output = iir.output_contract
    output_block = [
        f"- Format: {output.format}",
        f"- Language: {output.language or 'default'}",
    ]
    if output.max_words is not None:
        output_block.append(f"- Max words: {output.max_words}")
    if output.sections:
        output_block.append("- Sections:")
        output_block.extend(f"  - {section}" for section in output.sections)
    if output.json_schema is not None:
        output_block.append("- JSON Schema:")
        output_block.append("```json")
        output_block.append(dump_json(output.json_schema))
        output_block.append("```")

    parts = [
        f"# {iir.metadata.get('title') or iir.metadata.get('name', 'GovernSpec Task')}",
        "",
        "## Goal",
        iir.normalized_goal,
        "",
        "## Context",
        render_markdown_list(
            [f"Domain: {iir.resolved_context.get('domain', '')}"]
            + [f"Fact: {item}" for item in iir.resolved_context.get("facts", [])]
            + [f"Assumption: {item}" for item in iir.resolved_context.get("assumptions", [])]
        ),
        "",
        "## Inputs",
        render_markdown_list(
            [
                f"{item['name']} ({item['type']}): {item['path']} [privacy={item['privacy']}]"
                for item in iir.resolved_inputs
            ]
        ),
        "",
        "## Permissions",
        render_markdown_list(_permission_lines(iir)),
        "",
        "## Constraints",
        render_markdown_list(iir.merged_constraints),
        "",
        "## Evidence Policy",
        render_markdown_list(_evidence_lines(iir)),
        "",
        "## Output Contract",
        "\n".join(output_block),
        "",
        "## Human Confirmation Rules",
        render_markdown_list(
            [f"{item['when']} -> {item['action']}" for item in iir.human_gates]
        ),
        "",
        "## Verification",
        render_markdown_list([item["name"] for item in iir.test_contract]),
        "",
        "## Execution Principles",
        (
            "- When information is insufficient but the core result is still possible, "
            "list assumptions and continue."
        ),
        (
            "- When information is insufficient and it materially affects the result, "
            "or involves money, law, health, safety, privacy, or high-permission "
            "actions, request human confirmation first."
        ),
        (
            "- Do not fabricate facts, data, sources, or information that the user "
            "did not provide."
        ),
    ]
    return "\n".join(parts).strip()


def _compile_openai_json(iir: NormalizedIntent) -> str:
    payload = {
        "name": iir.metadata.get("name"),
        "instructions": _compile_prompt(iir),
        "input_contract": {
            "metadata": iir.metadata,
            "context": iir.resolved_context,
            "inputs": iir.resolved_inputs,
            "evidence": iir.evidence_policy,
        },
        "output_contract": iir.output_contract.model_dump(by_alias=True),
        "permissions": iir.resolved_permissions,
        "constraints": iir.merged_constraints,
        "human_gates": iir.human_gates,
        "tests": iir.test_contract,
    }
    return dump_json(payload)


def _compile_openai_structured(iir: NormalizedIntent) -> str:
    schema = _require_json_schema(iir, target="openai-structured")
    payload = {
        "type": "json_schema",
        "json_schema": {
            "name": iir.metadata.get("name", "governspec_output"),
            "description": iir.metadata.get("description", ""),
            "strict": True,
            "schema": schema,
        },
    }
    return dump_json(payload)


def _compile_gemini_structured(iir: NormalizedIntent) -> str:
    schema = _require_json_schema(iir, target="gemini-structured")
    _ensure_gemini_schema_supported(schema)
    payload = {
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseJsonSchema": schema,
        }
    }
    return dump_json(payload)


def _compile_instruction_markdown(iir: NormalizedIntent, title: str) -> str:
    parts = [f"# {title}", ""]
    for heading, items in _instruction_sections(iir):
        parts.append(f"## {heading}")
        if heading == "Project Goal":
            parts.append(iir.normalized_goal)
        else:
            parts.append(render_markdown_list(items))
        parts.append("")
    return "\n".join(parts).strip()


def _compile_cursor_rules_bundle(iir: NormalizedIntent) -> dict[str, str]:
    body = _render_rule_document(
        iir,
        title="GovernSpec Cursor Rules",
    )
    rendered = "\n".join(
        [
            "---",
            "description: GovernSpec-generated project rules",
            "alwaysApply: true",
            "---",
            "",
            body,
        ]
    ).strip()
    return {".cursor/rules/governspec.mdc": rendered}


def _compile_antigravity_rules_bundle(iir: NormalizedIntent) -> dict[str, str]:
    return {
        ".agents/rules/governspec.md": _render_rule_document(
            iir,
            title="GovernSpec Antigravity Rules",
        )
    }


def _render_rule_document(iir: NormalizedIntent, *, title: str) -> str:
    parts = [f"# {title}", ""]
    for heading, items in _instruction_sections(iir):
        parts.append(f"## {heading}")
        if heading == "Project Goal":
            parts.append(iir.normalized_goal)
        else:
            parts.append(render_markdown_list(items))
        parts.append("")
    return "\n".join(parts).strip()


def _instruction_sections(iir: NormalizedIntent) -> list[tuple[str, list[str]]]:
    return [
        ("Project Goal", []),
        ("Working Constraints", iir.merged_constraints),
        ("Allowed and Forbidden Operations", _permission_lines(iir)),
        (
            "Human Confirmation Rules",
            [f"{item['when']} -> {item['action']}" for item in iir.human_gates],
        ),
        ("Output Expectations", _output_expectation_lines(iir)),
        ("Verification Steps", [item["name"] for item in iir.test_contract]),
    ]


def _compile_skill_bundle(iir: NormalizedIntent) -> dict[str, str]:
    skill_md = "\n".join(
        [
            "---",
            f"name: {iir.metadata.get('name', 'governspec-skill')}",
            f"description: {iir.metadata.get('description', iir.normalized_goal)}",
            "---",
            "",
            "# Skill",
            "",
            "## Goal",
            iir.normalized_goal,
            "",
            "## Constraints",
            render_markdown_list(iir.merged_constraints),
            "",
            "## Human Confirmation Rules",
            render_markdown_list(
                [f"{item['when']} -> {item['action']}" for item in iir.human_gates]
            ),
            "",
            "## Output Expectations",
            render_markdown_list(_output_expectation_lines(iir)),
        ]
    ).strip()
    return {
        "SKILL.md": skill_md,
        "references/README.md": "Add reusable reference material for this skill here.\n",
        "scripts/README.md": "Add optional helper scripts for this skill here.\n",
    }


def _compile_mcp_plan(iir: NormalizedIntent) -> str:
    permissions = iir.resolved_permissions
    tool_permissions = permissions.get("tools", {})
    permission_map = {
        "web": permissions.get("web", False),
        "network": permissions.get("network", False),
        "filesystem.read": permissions.get("filesystem", {}).get("read", False),
        "filesystem.write": permissions.get("filesystem", {}).get("write", False),
        "tools.send_email": tool_permissions.get("send_email", False),
        "tools.read_calendar": tool_permissions.get("read_calendar", False),
        "tools.read_gmail": tool_permissions.get("read_gmail", False),
        "tools.create_file": tool_permissions.get("create_file", False),
        "tools.delete_file": tool_permissions.get("delete_file", False),
        "tools.purchase": tool_permissions.get("purchase", False),
    }
    payload = {
        "kind": "MCPExecutionPlan",
        "version": "0.1",
        "task": iir.normalized_goal,
        "allowed_tools": [name for name, allowed in permission_map.items() if allowed],
        "denied_tools": [name for name, allowed in permission_map.items() if not allowed],
        "required_user_consents": [
            item["when"] for item in iir.human_gates if item["action"] == "ask_confirmation"
        ],
        "sensitive_resources": [
            item["path"] for item in iir.resolved_inputs if item.get("privacy") == "confidential"
        ],
        "risk_level": _risk_level(iir),
        "human_gates": iir.human_gates,
        "constraint_loss": iir.target_capability_notes.get("mcp-plan", []),
        "resources": iir.resolved_inputs,
    }
    return dump_json(payload)


def _require_json_schema(iir: NormalizedIntent, *, target: str) -> dict[str, Any]:
    if iir.output_contract.format != "json" or iir.output_contract.json_schema is None:
        raise GovernSpecCompileError(
            f"{target} requires output.format=json with output.schema.",
            suggestion="Set output.format to json and define output.schema before compiling.",
        )
    return iir.output_contract.json_schema


def _ensure_gemini_schema_supported(schema: dict[str, Any]) -> None:
    unsupported: list[str] = []

    def walk(node: Any, path: str) -> None:
        if not isinstance(node, dict):
            unsupported.append(f"{path}: schema node must be an object")
            return

        for key, value in node.items():
            keyword_path = f"{path}.{key}"
            if key not in _GEMINI_ALLOWED_SCHEMA_KEYS:
                unsupported.append(f"{keyword_path}: unsupported keyword")
                continue

            if key == "type":
                if not isinstance(value, str) or value not in _GEMINI_ALLOWED_TYPES:
                    unsupported.append(f"{keyword_path}: unsupported type value")
            elif key == "properties":
                if not isinstance(value, dict):
                    unsupported.append(f"{keyword_path}: properties must be an object")
                else:
                    for property_name, property_schema in value.items():
                        walk(property_schema, f"{keyword_path}.{property_name}")
            elif key == "items":
                if isinstance(value, dict):
                    walk(value, keyword_path)
                else:
                    unsupported.append(f"{keyword_path}: items must be a schema object")
            elif key in {"required", "enum"}:
                if not isinstance(value, list):
                    unsupported.append(f"{keyword_path}: value must be an array")
            elif key in {"minItems", "maxItems"}:
                if not isinstance(value, int):
                    unsupported.append(f"{keyword_path}: value must be an integer")
            elif key == "description":
                if not isinstance(value, str):
                    unsupported.append(f"{keyword_path}: description must be a string")
            elif key == "additionalProperties":
                if not isinstance(value, bool):
                    unsupported.append(
                        f"{keyword_path}: only boolean additionalProperties is supported"
                    )

    walk(schema, "$")

    if unsupported:
        raise GovernSpecCompileError(
            "gemini-structured does not support the current output.schema.",
            suggestion=(
                "Use only Gemini-supported JSON Schema keywords or switch to "
                "openai-structured."
            ),
            details={"unsupported_keywords": unsupported},
        )


def _permission_lines(iir: NormalizedIntent) -> list[str]:
    permissions = iir.resolved_permissions
    tool_permissions = permissions.get("tools", {})
    return [
        f"Web access: {'allowed' if permissions.get('web') else 'forbidden'}",
        f"Network access: {'allowed' if permissions.get('network') else 'forbidden'}",
        (
            "Filesystem read: "
            f"{'allowed' if permissions.get('filesystem', {}).get('read') else 'forbidden'}"
        ),
        (
            "Filesystem write: "
            f"{'allowed' if permissions.get('filesystem', {}).get('write') else 'forbidden'}"
        ),
        f"Tool send_email: {'allowed' if tool_permissions.get('send_email') else 'forbidden'}",
        (
            "Tool read_calendar: "
            f"{'allowed' if tool_permissions.get('read_calendar') else 'forbidden'}"
        ),
        f"Tool read_gmail: {'allowed' if tool_permissions.get('read_gmail') else 'forbidden'}",
        (
            "Tool create_file: "
            f"{'allowed' if tool_permissions.get('create_file') else 'forbidden'}"
        ),
        (
            "Tool delete_file: "
            f"{'allowed' if tool_permissions.get('delete_file') else 'forbidden'}"
        ),
        f"Tool purchase: {'allowed' if tool_permissions.get('purchase') else 'forbidden'}",
    ]


def _evidence_lines(iir: NormalizedIntent) -> list[str]:
    evidence = iir.evidence_policy
    lines = [
        f"Require sources: {evidence.get('require_sources', False)}",
        f"Mark uncertainty: {evidence.get('mark_uncertainty', False)}",
    ]
    lines.extend(f"Distinguish: {item}" for item in evidence.get("distinguish", []))
    return lines


def _output_expectation_lines(iir: NormalizedIntent) -> list[str]:
    output = iir.output_contract
    lines = [f"Format: {output.format}"]
    if output.language:
        lines.append(f"Language: {output.language}")
    if output.max_words is not None:
        lines.append(f"Max words: {output.max_words}")
    if output.sections:
        lines.extend(f"Section: {item}" for item in output.sections)
    if output.json_schema is not None:
        lines.append("JSON Schema is required.")
    return lines


def _risk_level(iir: NormalizedIntent) -> str:
    permissions = iir.resolved_permissions
    tool_permissions = permissions.get("tools", {})
    human_gate_needed = any(
        [
            tool_permissions.get("send_email"),
            tool_permissions.get("delete_file"),
            tool_permissions.get("purchase"),
            tool_permissions.get("read_gmail"),
            tool_permissions.get("read_calendar"),
        ]
    )
    if human_gate_needed and not iir.human_gates:
        return "high"
    if human_gate_needed:
        return "high"
    if any(
        [
            permissions.get("web"),
            permissions.get("network"),
            permissions.get("filesystem", {}).get("write"),
            tool_permissions.get("create_file"),
            any(item.get("privacy") == "confidential" for item in iir.resolved_inputs),
        ]
    ):
        return "medium"
    return "low"
