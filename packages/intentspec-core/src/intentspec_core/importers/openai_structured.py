"""Import an OpenAI Structured Outputs payload into an IntentSpec draft."""

from __future__ import annotations

from typing import Any

from intentspec_core.common.errors import IntentSpecParseError
from intentspec_core.importers._parsing import build_draft_payload, default_permissions


def import_openai_structured(data: dict[str, Any]) -> dict[str, Any]:
    """Convert an OpenAI Structured Outputs JSON payload to a draft IntentSpec dict.

    Expected input shape::

        {
          "type": "json_schema",
          "json_schema": {
            "name": "...",
            "description": "...",
            "strict": true,
            "schema": { ... }
          }
        }
    """
    json_schema_block = data.get("json_schema")
    if not isinstance(json_schema_block, dict):
        raise IntentSpecParseError(
            "Missing or invalid 'json_schema' key in OpenAI structured payload.",
            suggestion="Provide a valid OpenAI Structured Outputs JSON with a 'json_schema' key.",
        )

    schema = json_schema_block.get("schema")
    if not isinstance(schema, dict) or not schema:
        raise IntentSpecParseError(
            "Missing or empty 'json_schema.schema' in OpenAI structured payload.",
            suggestion="Provide a JSON Schema under 'json_schema.schema'.",
        )

    name = json_schema_block.get("name", "imported_intent")
    description = json_schema_block.get("description", "")

    tests = _build_json_tests(schema)
    goal = description or f"Produce JSON output conforming to the {name} schema."

    return build_draft_payload(
        goal=goal,
        constraints=["Do not fabricate facts."],
        permissions=default_permissions(),
        human_gates=[],
        output_spec={"format": "json", "schema": schema},
        tests=tests,
        title=description or name,
        name=name,
        audience=["Downstream system"],
    )


def _build_json_tests(schema: dict[str, Any]) -> list[dict[str, Any]]:
    tests: list[dict[str, Any]] = [
        {"name": "Must match JSON schema", "assert": [{"type": "json_schema"}]},
    ]
    for field_name in schema.get("required", []):
        tests.append(
            {
                "name": f"Field '{field_name}' must exist",
                "assert": [{"type": "json_path_exists", "path": f"$.{field_name}"}],
            }
        )
    return tests
