"""Custom errors for IntentSpec."""

from __future__ import annotations

from typing import Any


class IntentSpecError(Exception):
    """Base error for IntentSpec."""

    def __init__(
        self,
        message: str,
        *,
        suggestion: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.suggestion = suggestion
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "suggestion": self.suggestion,
            "details": self.details,
        }

    def __str__(self) -> str:
        return self.message


class IntentSpecFileError(IntentSpecError):
    """Raised when an IntentSpec file cannot be accessed."""


class IntentSpecParseError(IntentSpecError):
    """Raised when YAML cannot be parsed."""


class IntentSpecValidationError(IntentSpecError):
    """Raised when a parsed spec is structurally invalid."""


class IntentSpecCompileError(IntentSpecError):
    """Raised when compilation fails."""


class IntentSpecTestError(IntentSpecError):
    """Raised when output testing cannot be completed."""
