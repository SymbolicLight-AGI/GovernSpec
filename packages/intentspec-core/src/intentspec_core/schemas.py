"""JSON Schema generation for IntentSpec v0.1."""

from __future__ import annotations

from pydantic import RootModel

from intentspec_core.spec.models import IntentDocument


class IntentDocumentSchema(RootModel[IntentDocument]):
    """Wrapper model for schema generation."""


def generate_json_schema() -> dict:
    schema = IntentDocumentSchema.model_json_schema()
    schema["title"] = "IntentSpecDocument"
    return schema
