"""GovernSpec core package."""

from governspec_core.common.errors import (
    GovernSpecCompileError,
    GovernSpecError,
    GovernSpecFileError,
    GovernSpecParseError,
    GovernSpecTestError,
    GovernSpecValidationError,
)
from governspec_core.common.utils import heuristic_draft_payload
from governspec_core.doctor import DoctorReport, run_doctor
from governspec_core.examples import ExampleFile, copy_example, list_examples
from governspec_core.iir.builder import build_iir, inspect_document, inspect_iir
from governspec_core.iir.models import NormalizedIntent
from governspec_core.importers.reverse import (
    SUPPORTED_IMPORT_TYPES,
    import_from_artifact,
    import_from_string,
)
from governspec_core.imports.resolver import resolve_document_imports, resolve_imports
from governspec_core.schemas import generate_json_schema
from governspec_core.spec.models import GovernDocument, GovernPack, GovernSpec
from governspec_core.spec.parser import load_document, load_spec
from governspec_core.targets.compiler import (
    SUPPORTED_TARGETS,
    CompiledArtifact,
    compile_target,
)
from governspec_core.testing.tester import TestReport, test_output
from governspec_core.validator import ValidationReport, validate_document, validate_spec

__all__ = [
    "CompiledArtifact",
    "DoctorReport",
    "ExampleFile",
    "GovernDocument",
    "GovernPack",
    "GovernSpec",
    "GovernSpecCompileError",
    "GovernSpecError",
    "GovernSpecFileError",
    "GovernSpecParseError",
    "GovernSpecTestError",
    "GovernSpecValidationError",
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
