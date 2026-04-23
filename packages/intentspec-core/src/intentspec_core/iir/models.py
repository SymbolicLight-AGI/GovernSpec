"""IIR models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class OutputContract(BaseModel):
    format: str
    language: str | None = None
    max_words: int | None = None
    sections: list[str] = Field(default_factory=list)
    json_schema: dict[str, Any] | None = Field(default=None, alias="schema")

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class NormalizedIntent(BaseModel):
    source_path: str
    metadata: dict[str, Any]
    normalized_goal: str
    resolved_context: dict[str, Any]
    resolved_inputs: list[dict[str, Any]]
    resolved_permissions: dict[str, Any]
    merged_constraints: list[str]
    evidence_policy: dict[str, Any]
    output_contract: OutputContract
    human_gates: list[dict[str, Any]]
    test_contract: list[dict[str, Any]]
    risk_signals: list[str]
    target_capability_notes: dict[str, list[str]]

    model_config = ConfigDict(extra="forbid")
