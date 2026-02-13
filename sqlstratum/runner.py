"""SQLite execution runner."""
from __future__ import annotations

import logging
import os
import sqlite3
import time
from contextlib import contextmanager
from typing import Any, Dict, Iterable, Optional

from . import ast
from .compile import compile
from .hydrate import hydrate_rows


_LOGGER = logging.getLogger("sqlstratum")
_DEBUG_TRUE = {"1", "true", "yes"}
_MAX_PARAM_REPR_LEN = 200
_MAX_BLOB_PREVIEW = 64


def _env_debug_enabled() -> bool:
    value = os.getenv("SQLSTRATUM_DEBUG", "")
    return value.lower() in _DEBUG_TRUE


def _debug_enabled() -> bool:
    return _env_debug_enabled() and _LOGGER.isEnabledFor(logging.DEBUG)


def _truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return f"{value[:limit]}...<{len(value) - limit} more>"


def _safe_param_repr(value: Any) -> str:
    if isinstance(value, (bytes, bytearray, memoryview)):
        data = bytes(value)
        preview = data[:_MAX_BLOB_PREVIEW]
        rep = repr(preview)
        if len(data) > _MAX_BLOB_PREVIEW:
            rep = f"{rep}...<{len(data) - _MAX_BLOB_PREVIEW} more bytes>"
        return rep
    rep = repr(value)
    return _truncate(rep, _MAX_PARAM_REPR_LEN)


def _render_params(params: Dict[str, Any]) -> str:
    if not params:
        return "{}"
    items = ", ".join(f"{key}={_safe_param_repr(params[key])}" for key in sorted(params))
    return "{" + items + "}"


def _debug_log(compiled: ast.Compiled, duration_ms: float) -> None:
    _LOGGER.debug(
        "SQL: %s | params=%s | duration_ms=%.3f",
        compiled.sql,
        _render_params(compiled.params),
        duration_ms,
    )


class Runner:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection
        self.connection.row_factory = sqlite3.Row
        self._tx_depth = 0

    @classmethod
    def connect(cls, path: str) -> "Runner":
        return cls(sqlite3.connect(path))

    def exec_ddl(self, sql: str) -> None:
        cur = self.connection.cursor()
        cur.execute(sql)
        if self._tx_depth == 0:
            self.connection.commit()

    def fetch_all(self, query: ast.SelectQuery) -> list[Any]:
        compiled = compile(query)
        log_enabled = _debug_enabled()
        start = time.perf_counter() if log_enabled else 0.0
        cur = self.connection.cursor()
        cur.execute(compiled.sql, compiled.params)
        rows = cur.fetchall()
        if log_enabled:
            _debug_log(compiled, (time.perf_counter() - start) * 1000)
        return hydrate_rows(rows, query.projections, query.hydration or dict)

    def fetch_one(self, query: ast.SelectQuery) -> Optional[Any]:
        compiled = compile(query)
        log_enabled = _debug_enabled()
        start = time.perf_counter() if log_enabled else 0.0
        cur = self.connection.cursor()
        cur.execute(compiled.sql, compiled.params)
        row = cur.fetchone()
        if log_enabled:
            _debug_log(compiled, (time.perf_counter() - start) * 1000)
        if row is None:
            return None
        return hydrate_rows([row], query.projections, query.hydration or dict)[0]

    def scalar(self, query: ast.SelectQuery) -> Optional[Any]:
        compiled = compile(query)
        log_enabled = _debug_enabled()
        start = time.perf_counter() if log_enabled else 0.0
        cur = self.connection.cursor()
        cur.execute(compiled.sql, compiled.params)
        row = cur.fetchone()
        if log_enabled:
            _debug_log(compiled, (time.perf_counter() - start) * 1000)
        if row is None:
            return None
        return row[0]

    def execute(self, query: Any) -> ast.ExecutionResult:
        compiled = compile(query)
        log_enabled = _debug_enabled()
        start = time.perf_counter() if log_enabled else 0.0
        cur = self.connection.cursor()
        cur.execute(compiled.sql, compiled.params)
        if self._tx_depth == 0:
            self.connection.commit()
        if log_enabled:
            _debug_log(compiled, (time.perf_counter() - start) * 1000)
        return ast.ExecutionResult(rowcount=cur.rowcount, lastrowid=cur.lastrowid)

    @contextmanager
    def transaction(self):
        self._tx_depth += 1
        try:
            yield
        except Exception:
            self.connection.rollback()
            raise
        else:
            self.connection.commit()
        finally:
            self._tx_depth -= 1
