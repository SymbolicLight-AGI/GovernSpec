"""JSON Schema generation for GovernSpec v0.1."""

from __future__ import annotations

from pydantic import RootModel

from governspec_core.spec.models import GovernDocument


class GovernDocumentSchema(RootModel[GovernDocument]):
    """Wrapper model for schema generation."""


def generate_json_schema() -> dict:
    schema = GovernDocumentSchema.model_json_schema()
    schema["title"] = "GovernSpecDocument"
    return schema
