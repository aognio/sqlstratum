"""SQLite dialect registration."""
from .compiler import SQLiteCompiler
from ..registry import register_dialect

register_dialect("sqlite", SQLiteCompiler())

__all__ = ["SQLiteCompiler"]
