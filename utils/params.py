"""Structured parameter helpers for build123d dataclass models.

Produces standard ``dataclasses.Field.metadata`` consumed by Code CAD Studio
(``label``, ``description``, ``unit``, ``min``, ``max``, ``step``, ``when``)
with zero external dependencies.
"""

from __future__ import annotations

from dataclasses import field
from typing import Any, Callable, TypeVar, cast

T = TypeVar("T")


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
