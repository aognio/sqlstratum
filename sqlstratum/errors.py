"""Project-specific exceptions."""
from __future__ import annotations

from typing import Optional


class SQLStratumError(Exception):
    """Base error for SQLStratum."""


class UnsupportedDialectFeatureError(SQLStratumError):
    """Raised when a query feature is not supported by the selected dialect."""

    def __init__(self, dialect: str, feature: str, hint: Optional[str] = None):
        message = f"Dialect '{dialect}' does not support feature: {feature}"
        if hint:
            message = f"{message}. {hint}"
        super().__init__(message)
