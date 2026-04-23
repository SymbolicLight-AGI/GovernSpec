"""Pydantic models for IntentSpec v0.1."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, TypeAdapter, field_validator


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class Metadata(StrictBaseModel):
    name: str = Field(..., min_length=1)
    title: str = ""
    description: str = ""
    owner: str = ""


class Task(StrictBaseModel):
    goal: str = Field(..., min_length=1)
    audience: list[str] = Field(default_factory=list)
    priority: Literal["low", "medium", "high"] = "medium"

    @field_validator("goal")
    @classmethod
    def validate_goal(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("task.goal must not be empty")
        return stripped


class Context(StrictBaseModel):
    domain: str = ""
    facts: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    glossary: dict[str, str] = Field(default_factory=dict)


class InputSpec(StrictBaseModel):
    name: str = Field(..., min_length=1)
    type: str = Field(..., min_length=1)
    path: str = Field(..., min_length=1)
    required: bool = False
    privacy: str = "internal"


class FilesystemPermission(StrictBaseModel):
    read: bool = False
    write: bool = False


class ToolPermissions(StrictBaseModel):
    send_email: bool = False
    read_calendar: bool = False
    read_gmail: bool = False
    create_file: bool = False
    delete_file: bool = False
    purchase: bool = False


class Permissions(StrictBaseModel):
    web: bool = False
    filesystem: FilesystemPermission = Field(default_factory=FilesystemPermission)
    network: bool = False
    tools: ToolPermissions = Field(default_factory=ToolPermissions)


class Evidence(StrictBaseModel):
    require_sources: bool = False
    mark_uncertainty: bool = False
    distinguish: list[str] = Field(default_factory=list)


class Quality(StrictBaseModel):
    tone: list[str] = Field(default_factory=list)
    must_include: list[str] = Field(default_factory=list)
    must_avoid: list[str] = Field(default_factory=list)


class HumanGate(StrictBaseModel):
    when: str = Field(..., min_length=1)
    action: str = Field(..., min_length=1)


class Assertion(StrictBaseModel):
    type: str = Field(..., min_length=1)
    path: str | None = None
    value: str | int | None = None
    pattern: str | None = None


class TestCase(StrictBaseModel):
    name: str = Field(..., min_length=1)
    assertions: list[Assertion] = Field(..., alias="assert", min_length=1)


class MarkdownOutput(StrictBaseModel):
    format: Literal["markdown"]
    language: str = Field(..., min_length=1)
    max_words: int = Field(..., gt=0)
    sections: list[str] = Field(..., min_length=1)


class TextOutput(StrictBaseModel):
    format: Literal["text"]
    language: str = Field(..., min_length=1)
    max_words: int = Field(..., gt=0)
    sections: list[str] = Field(default_factory=list)


class JsonOutput(StrictBaseModel):
    format: Literal["json"]
    json_schema: dict[str, Any] = Field(..., alias="schema")
    language: str | None = None

    @field_validator("json_schema")
    @classmethod
    def validate_schema(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not value:
            raise ValueError("output.schema must not be empty")
        return value


OutputSpec = Annotated[MarkdownOutput | TextOutput | JsonOutput, Field(discriminator="format")]


class BaseDocument(StrictBaseModel):
    version: Literal["0.1"]
    imports: list[str] = Field(default_factory=list)

    _source_path: Path | None = PrivateAttr(default=None)
    _resolved_imports: list[Path] = PrivateAttr(default_factory=list)


class IntentSpec(BaseDocument):
    kind: Literal["IntentSpec"]
    metadata: Metadata
    task: Task
    context: Context = Field(default_factory=Context)
    inputs: list[InputSpec] = Field(default_factory=list)
    permissions: Permissions = Field(default_factory=Permissions)
    constraints: list[str] = Field(default_factory=list)
    evidence: Evidence = Field(default_factory=Evidence)
    output: OutputSpec
    quality: Quality = Field(default_factory=Quality)
    human_gates: list[HumanGate] = Field(default_factory=list)
    tests: list[TestCase] = Field(default_factory=list)
class IntentPack(BaseDocument):
    kind: Literal["IntentPack"]
    metadata: Metadata
    permissions: Permissions | None = None
    constraints: list[str] = Field(default_factory=list)
    evidence: Evidence | None = None
    quality: Quality | None = None
    human_gates: list[HumanGate] = Field(default_factory=list)
    tests: list[TestCase] = Field(default_factory=list)


IntentDocument = IntentSpec | IntentPack
IntentDocumentAdapter: TypeAdapter[IntentDocument] = TypeAdapter(IntentDocument)
