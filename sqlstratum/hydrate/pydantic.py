"""Optional Pydantic v2 hydration adapters."""
from __future__ import annotations

import importlib
from typing import Any, Mapping, Protocol, TypeVar

_INSTALL_MESSAGE = "Install with: pip install sqlstratum[pydantic]"


class _PydanticModel(Protocol):
    @classmethod
    def model_validate(cls, obj: Any) -> Any:  # pragma: no cover - protocol signature
        ...


TModel = TypeVar("TModel", bound=_PydanticModel)


def _import_pydantic():
    return importlib.import_module("pydantic")


def is_pydantic_available() -> bool:
    try:
        _import_pydantic()
        return True
    except Exception:
        return False


def hydrate_model(model_cls: type[TModel], data: Mapping[str, Any]) -> TModel:
    try:
        _import_pydantic()
    except Exception as exc:
        raise RuntimeError(_INSTALL_MESSAGE) from exc
    return model_cls.model_validate(dict(data))


def hydrate_models(model_cls: type[TModel], rows: list[Mapping[str, Any]]) -> list[TModel]:
    return [hydrate_model(model_cls, row) for row in rows]


class _PydanticHydrateWrapper:
    def __init__(self, query: Any) -> None:
        self._query = query

    def hydrate(self, model_cls: type[TModel]) -> Any:
        return self._query.hydrate(lambda m: hydrate_model(model_cls, m))


def using_pydantic(query: Any) -> _PydanticHydrateWrapper:
    return _PydanticHydrateWrapper(query)
