"""Hydration utilities."""
from __future__ import annotations

from dataclasses import is_dataclass
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from ..expr import AliasExpr, Function
from ..meta import Column
from ..types import HydrationTarget


class HydrationError(ValueError):
    pass


def projection_keys(projections: Sequence[Any]) -> List[str]:
    keys: List[str] = []
    for proj in projections:
        key = _projection_key(proj)
        if key in keys:
            raise HydrationError(f"Duplicate projection key '{key}'. Use AS() to disambiguate.")
        keys.append(key)
    return keys


def _projection_key(proj: Any) -> str:
    if isinstance(proj, AliasExpr):
        return proj.alias
    if isinstance(proj, Column):
        return proj.name
    if isinstance(proj, Function):
        raise HydrationError("Aggregate expressions require AS('alias') for hydration")
    raise HydrationError("Projection requires AS('alias') for hydration")


def hydrate_rows(
    rows: Iterable[Mapping[str, Any]],
    projections: Sequence[Any],
    target: HydrationTarget,
) -> List[Any]:
    keys = projection_keys(projections)
    mapped: List[Dict[str, Any]] = []
    for row in rows:
        mapped.append({k: row[k] for k in keys})

    if target is None or target is dict:
        return mapped

    if is_dataclass(target):
        return [target(**m) for m in mapped]

    if callable(target):
        return [target(m) for m in mapped]

    raise HydrationError("Unsupported hydration target")
