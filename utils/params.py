"""Structured parameter helpers for build123d dataclass models.

Produces standard ``dataclasses.Field.metadata`` consumed by Code CAD Studio
(``label``, ``description``, ``unit``, ``min``, ``max``, ``step``, ``when``)
and optional root-class ``__default_preset__`` metadata with zero external
dependencies.
"""

from __future__ import annotations

from dataclasses import field
from typing import Any, Callable, TypeVar, cast

T = TypeVar("T")


def default_preset(
    label: str,
    *,
    desc: str | None = None,
) -> Callable[[type[T]], type[T]]:
    """Attach a friendly preset label and description to a root Params dataclass."""

    def _decorator(cls: type[T]) -> type[T]:
        meta: dict[str, str] = {"label": label.strip()}
        if desc is not None and desc.strip():
            meta["description"] = desc.strip()
        setattr(cls, "__default_preset__", meta)
        return cls

    return _decorator


def param(
    default: T,
    *,
    label: str | None = None,
    desc: str | None = None,
    unit: str | None = None,
    min: int | float | None = None,
    max: int | float | None = None,
    step: int | float | None = None,
    when: dict[str, Any] | None = None,
) -> T:
    """Define a parametric dataclass field with structured UI metadata."""
    meta: dict[str, Any] = {}
    if label is not None:
        meta["label"] = label
    if desc is not None:
        meta["description"] = desc
    if unit is not None:
        meta["unit"] = unit
    if min is not None:
        meta["min"] = min
    if max is not None:
        meta["max"] = max
    if step is not None:
        meta["step"] = step
    if when is not None:
        meta["when"] = when
    return cast(T, field(default=default, metadata=meta))


def group(
    factory: Callable[[], T],
    *,
    label: str | None = None,
    desc: str | None = None,
    when: dict[str, Any] | None = None,
) -> T:
    """Define a nested parameter-group dataclass field with optional UI metadata."""
    meta: dict[str, Any] = {}
    if label is not None:
        meta["label"] = label
    if desc is not None:
        meta["description"] = desc
    if when is not None:
        meta["when"] = when
    return cast(T, field(default_factory=factory, metadata=meta))
