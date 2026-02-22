"""MySQL dialect registration."""
from .compiler import MySQLCompiler
from ..registry import register_dialect

register_dialect("mysql", MySQLCompiler())

__all__ = ["MySQLCompiler"]
