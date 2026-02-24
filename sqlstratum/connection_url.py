"""Connection URL parsing helpers for optional runner constructors."""
from __future__ import annotations

from typing import Dict
from urllib.parse import unquote, urlparse


def parse_sqlite_url(url: str) -> str:
    if not url:
        raise ValueError("SQLite URL must be a non-empty string")
    parsed = urlparse(url)
    if parsed.scheme != "sqlite":
        raise ValueError("Invalid SQLite URL scheme. Expected sqlite://")
    if parsed.netloc:
        raise ValueError("SQLite URL must not include a hostname")
    if parsed.query or parsed.fragment:
        raise ValueError("SQLite URL query parameters and fragments are not supported")
    if not parsed.path:
        raise ValueError("SQLite URL must include a database path")

    if url == "sqlite:///:memory:":
        return ":memory:"

    if url.startswith("sqlite:////"):
        path = unquote(parsed.path)
        if path.startswith("//"):
            path = path[1:]
        if path in {"", "/"}:
            raise ValueError("SQLite URL must include a database path")
        return path

    if url.startswith("sqlite:///"):
        path = unquote(parsed.path.lstrip("/"))
        if not path:
            raise ValueError("SQLite URL must include a database path")
        return path

    raise ValueError("Unsupported SQLite URL format")


def parse_mysql_url(url: str, *, async_mode: bool) -> Dict[str, object]:
    if not url:
        raise ValueError("MySQL URL must be a non-empty string")
    parsed = urlparse(url)
    scheme = parsed.scheme
    allowed = {"mysql", "mysql+asyncmy" if async_mode else "mysql+pymysql"}
    if scheme not in allowed:
        expected = "mysql or mysql+asyncmy" if async_mode else "mysql or mysql+pymysql"
        raise ValueError(f"Invalid MySQL URL scheme. Expected {expected}")
    if parsed.query or parsed.fragment:
        raise ValueError("MySQL URL query parameters and fragments are not supported")

    if not parsed.hostname:
        raise ValueError("MySQL URL must include a host")
    if parsed.username in {None, ""}:
        raise ValueError("MySQL URL must include a username")
    if parsed.password in {None, ""}:
        raise ValueError("MySQL URL must include a password")

    try:
        port = parsed.port or 3306
    except ValueError as exc:
        raise ValueError("MySQL URL has an invalid port") from exc

    database = parsed.path.lstrip("/")
    if not database:
        raise ValueError("MySQL URL must include a database name")
    if "/" in database:
        raise ValueError("MySQL URL must include a single database path segment")

    return {
        "host": parsed.hostname,
        "port": port,
        "user": unquote(parsed.username),
        "password": unquote(parsed.password),
        "database": unquote(database),
    }
