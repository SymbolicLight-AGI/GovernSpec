"""Import a Gemini structured output payload into a GovernSpec draft."""

from __future__ import annotations

from typing import Any

from governspec_core.common.errors import GovernSpecParseError
from governspec_core.importers._parsing import build_draft_payload, default_permissions


def import_gemini_structured(data: dict[str, Any]) -> dict[str, Any]:
    """Convert a Gemini structured output JSON payload to a draft GovernSpec dict.

    Expected input shape::

        {
          "generationConfig": {
            "responseMimeType": "application/json",
            "responseJsonSchema": { ... }
          }
        }
    """
    gen_config = data.get("generationConfig")
    if not isinstance(gen_config, dict):
        raise GovernSpecParseError(
            "Missing or invalid 'generationConfig' in Gemini structured payload.",
            suggestion=(
                "Provide a valid Gemini structured output JSON with a 'generationConfig' key."
            ),
        )

    schema = gen_config.get("responseJsonSchema")
    if not isinstance(schema, dict) or not schema:
        raise GovernSpecParseError(
            "Missing or empty 'generationConfig.responseJsonSchema'.",
            suggestion="Provide a JSON Schema under 'generationConfig.responseJsonSchema'.",
        )

    name = "imported_intent"
    description = schema.get("description", "")

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
