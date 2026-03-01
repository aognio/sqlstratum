"""MySQL asynchronous execution runner (asyncmy optional dependency)."""
from __future__ import annotations

import importlib
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, Mapping, Optional, Sequence

from . import ast
from .compile import compile
from .connection_url import parse_mysql_url
from .dialect_binding import unwrap_query
from .hydrate import hydrate_rows


_LOGGER = logging.getLogger("sqlstratum")
_DEBUG_TRUE = {"1", "true", "yes"}
_MAX_PARAM_REPR_LEN = 200
_MAX_BLOB_PREVIEW = 64
_INSTALL_MESSAGE = "Install with: pip install sqlstratum[asyncmy]"


def _import_asyncmy():
    return importlib.import_module("asyncmy")


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


def _resolve_output_shape(query: Any) -> tuple[Any, Any]:
    if isinstance(query, ast.SelectQuery):
        return query.projections, query.hydration
    if isinstance(query, ast.SetQuery):
        projections, hydration = _resolve_output_shape(query.left)
        return projections, query.hydration or hydration
    raise TypeError(f"Query does not produce rows: {type(query)}")


def _normalize_rows(cursor: Any, rows: Sequence[Any]) -> list[Mapping[str, Any]]:
    if not rows:
        return []
    first = rows[0]
    if isinstance(first, Mapping):
        return list(rows)  # type: ignore[return-value]
    columns = [desc[0] for desc in (cursor.description or [])]
    return [dict(zip(columns, row)) for row in rows]


def _normalize_one_row(cursor: Any, row: Any) -> Optional[Mapping[str, Any]]:
    if row is None:
        return None
    if isinstance(row, Mapping):
        return row
    columns = [desc[0] for desc in (cursor.description or [])]
    return dict(zip(columns, row))


class AsyncMySQLRunner:
    def __init__(self, connection: Any):
        self.connection = connection
        self._tx_depth = 0

    @classmethod
    async def connect(
        cls,
        *,
        url: Optional[str] = None,
        host: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        port: Optional[int] = None,
        **kwargs: Any,
    ) -> "AsyncMySQLRunner":
        if url and any(v is not None for v in (host, user, password, database, port)):
            raise ValueError("Provide either 'url' or individual connection parameters, not both")
        if not url and any(v is None for v in (host, user, password, database)):
            raise ValueError("Missing required connection parameters: host, user, password, database")
        if url:
            conn_args = parse_mysql_url(url, async_mode=True)
        else:
            conn_args = {
                "host": host,
                "user": user,
                "password": password,
                "database": database,
                "port": 3306 if port is None else port,
            }

        try:
            asyncmy = _import_asyncmy()
        except Exception as exc:
            raise RuntimeError(_INSTALL_MESSAGE) from exc

        kwargs.setdefault("autocommit", False)
        connection = await asyncmy.connect(**conn_args, **kwargs)
        return cls(connection)

    async def exec_ddl(self, sql: str) -> None:
        async with self.connection.cursor() as cur:
            await cur.execute(sql)
        if self._tx_depth == 0:
            await self.connection.commit()

    async def fetch_all(self, query: Any) -> list[Any]:
        unwrapped_query, _ = unwrap_query(query, "mysql")
        compiled = compile(unwrapped_query, dialect="mysql")
        projections, hydration = _resolve_output_shape(unwrapped_query)
        log_enabled = _debug_enabled()
        start = time.perf_counter() if log_enabled else 0.0
        async with self.connection.cursor() as cur:
            await cur.execute(compiled.sql, compiled.params)
            rows = _normalize_rows(cur, await cur.fetchall())
        if log_enabled:
            _debug_log(compiled, (time.perf_counter() - start) * 1000)
        return hydrate_rows(rows, projections, hydration or dict)

    async def fetch_one(self, query: Any) -> Optional[Any]:
        unwrapped_query, _ = unwrap_query(query, "mysql")
        compiled = compile(unwrapped_query, dialect="mysql")
        projections, hydration = _resolve_output_shape(unwrapped_query)
        log_enabled = _debug_enabled()
        start = time.perf_counter() if log_enabled else 0.0
        async with self.connection.cursor() as cur:
            await cur.execute(compiled.sql, compiled.params)
            row = _normalize_one_row(cur, await cur.fetchone())
        if log_enabled:
            _debug_log(compiled, (time.perf_counter() - start) * 1000)
        if row is None:
            return None
        return hydrate_rows([row], projections, hydration or dict)[0]

    async def scalar(self, query: Any) -> Optional[Any]:
        unwrapped_query, _ = unwrap_query(query, "mysql")
        compiled = compile(unwrapped_query, dialect="mysql")
        log_enabled = _debug_enabled()
        start = time.perf_counter() if log_enabled else 0.0
        async with self.connection.cursor() as cur:
            await cur.execute(compiled.sql, compiled.params)
            row = await cur.fetchone()
        if log_enabled:
            _debug_log(compiled, (time.perf_counter() - start) * 1000)
        if row is None:
            return None
        if isinstance(row, Mapping):
            return next(iter(row.values()), None)
        return row[0]

    async def execute(self, query: Any) -> ast.ExecutionResult:
        unwrapped_query, _ = unwrap_query(query, "mysql")
        compiled = compile(unwrapped_query, dialect="mysql")
        log_enabled = _debug_enabled()
        start = time.perf_counter() if log_enabled else 0.0
        async with self.connection.cursor() as cur:
            await cur.execute(compiled.sql, compiled.params)
            rowcount = cur.rowcount
            lastrowid = getattr(cur, "lastrowid", None)
        if self._tx_depth == 0:
            await self.connection.commit()
        if log_enabled:
            _debug_log(compiled, (time.perf_counter() - start) * 1000)
        return ast.ExecutionResult(rowcount=rowcount, lastrowid=lastrowid)

    @asynccontextmanager
    async def transaction(self):
        self._tx_depth += 1
        try:
            yield
        except Exception:
            await self.connection.rollback()
            raise
        else:
            await self.connection.commit()
        finally:
            self._tx_depth -= 1
