"""Custom errors for GovernSpec."""

from __future__ import annotations

from typing import Any


class GovernSpecError(Exception):
    """Base error for GovernSpec."""

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


class GovernSpecFileError(GovernSpecError):
    """Raised when a GovernSpec file cannot be accessed."""


class GovernSpecParseError(GovernSpecError):
    """Raised when YAML cannot be parsed."""


class GovernSpecValidationError(GovernSpecError):
    """Raised when a parsed spec is structurally invalid."""


class GovernSpecCompileError(GovernSpecError):
    """Raised when compilation fails."""


class GovernSpecTestError(GovernSpecError):
    """Raised when output testing cannot be completed."""
