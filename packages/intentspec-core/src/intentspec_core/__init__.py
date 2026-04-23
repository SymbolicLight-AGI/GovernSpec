"""IntentSpec core package."""

from intentspec_core.common.errors import (
    IntentSpecCompileError,
    IntentSpecError,
    IntentSpecFileError,
    IntentSpecParseError,
    IntentSpecTestError,
    IntentSpecValidationError,
)
from intentspec_core.common.utils import heuristic_draft_payload
from intentspec_core.doctor import DoctorReport, run_doctor
from intentspec_core.examples import ExampleFile, copy_example, list_examples
from intentspec_core.iir.builder import build_iir, inspect_document, inspect_iir
from intentspec_core.iir.models import NormalizedIntent
from intentspec_core.importers.reverse import (
    SUPPORTED_IMPORT_TYPES,
    import_from_artifact,
    import_from_string,
)
from intentspec_core.imports.resolver import resolve_document_imports, resolve_imports
from intentspec_core.schemas import generate_json_schema
from intentspec_core.spec.models import IntentDocument, IntentPack, IntentSpec
from intentspec_core.spec.parser import load_document, load_spec
from intentspec_core.targets.compiler import (
    SUPPORTED_TARGETS,
    CompiledArtifact,
    compile_target,
)
from intentspec_core.testing.tester import TestReport, test_output
from intentspec_core.validator import ValidationReport, validate_document, validate_spec

__all__ = [
    "CompiledArtifact",
    "DoctorReport",
    "ExampleFile",
    "IntentDocument",
    "IntentPack",
    "IntentSpec",
    "IntentSpecCompileError",
    "IntentSpecError",
    "IntentSpecFileError",
    "IntentSpecParseError",
    "IntentSpecTestError",
    "IntentSpecValidationError",
    "NormalizedIntent",
    "SUPPORTED_IMPORT_TYPES",
    "SUPPORTED_TARGETS",
    "TestReport",
    "ValidationReport",
    "build_iir",
    "compile_target",
    "copy_example",
    "generate_json_schema",
    "heuristic_draft_payload",
    "import_from_artifact",
    "import_from_string",
    "inspect_document",
    "inspect_iir",
    "list_examples",
    "load_document",
    "load_spec",
    "resolve_document_imports",
    "resolve_imports",
    "run_doctor",
    "test_output",
    "validate_document",
    "validate_spec",
]

__version__ = "0.1.0"
