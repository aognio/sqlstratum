"""MySQL-specific wrappers."""
from __future__ import annotations

from .dialect_binding import bind_dialect


def using_mysql(query):
    return bind_dialect(query, "mysql")
