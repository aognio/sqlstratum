"""Dialect registry and built-in dialect bootstrap."""
from .registry import get_dialect, list_dialects, register_dialect

# Register built-in dialect compilers when package is imported.
from . import sqlite  # noqa: F401
from . import mysql  # noqa: F401

__all__ = ["get_dialect", "list_dialects", "register_dialect"]
