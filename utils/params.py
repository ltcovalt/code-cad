"""Structured parameter helpers for build123d dataclass models.

Produces standard ``dataclasses.Field.metadata`` consumed by Code CAD Studio
(``label``, ``description``, ``unit``, ``min``, ``max``, ``step``, ``when``,
``component_preset``) and optional root-class ``__default_preset__`` metadata
with zero external dependencies.
"""

from __future__ import annotations

from dataclasses import field, fields, is_dataclass, replace
import inspect
import json
from pathlib import Path
import types
from typing import Any, Callable, Literal, TypeVar, Union, cast, get_args, get_origin, get_type_hints, overload

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
    item_label: str | None = None,
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
    if item_label is not None:
        meta["item_label"] = item_label
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


def param_list(
    factory: Callable[[], list[T]],
    *,
    label: str | None = None,
    desc: str | None = None,
    item_label: str | None = None,
    unit: str | None = None,
    min: int | float | None = None,
    max: int | float | None = None,
    step: int | float | None = None,
    when: dict[str, Any] | None = None,
) -> list[T]:
    """Define a list-of-items parameter field with structured UI metadata."""
    meta: dict[str, Any] = {}
    if label is not None:
        meta["label"] = label
    if desc is not None:
        meta["description"] = desc
    if item_label is not None:
        meta["item_label"] = item_label
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
    return cast(list[T], field(default_factory=factory, metadata=meta))


def _load_component_preset_params(factory: Callable[[], Any], preset_key: str) -> dict[str, Any]:
    """Load sparse ``params`` for ``preset_key`` from the component's presets.json, or {}."""
    try:
        src = inspect.getsourcefile(factory)
    except Exception:
        src = None
    if not src:
        return {}
    src_path = Path(src).resolve()
    parent = src_path.parent
    presets_path = (
        parent / "presets.json"
        if parent.name == src_path.stem
        else parent / f"{src_path.stem}.presets.json"
    )
    if not presets_path.is_file():
        return {}
    try:
        data = json.loads(presets_path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        return {}
    presets = data.get("presets")
    if not isinstance(presets, dict):
        return {}
    entry = presets.get(preset_key)
    if not isinstance(entry, dict):
        return {}
    raw_params = entry.get("params")
    return dict(raw_params) if isinstance(raw_params, dict) else {}


def _unwrap_optional_type(tp: Any) -> Any:
    origin = get_origin(tp)
    if origin is Union or origin is types.UnionType:
        non_none = [a for a in get_args(tp) if a is not type(None)]
        if len(non_none) == 1:
            return non_none[0]
    return tp


def _apply_group_overrides(instance: T, overrides: dict[str, Any]) -> T:
    """Return a copy of ``instance`` with sparse ``overrides`` applied recursively."""
    if not is_dataclass(instance) or not isinstance(overrides, dict) or not overrides:
        return instance
    try:
        hints = get_type_hints(type(instance))
    except Exception:
        hints = {}

    updates: dict[str, Any] = {}
    for f in fields(instance):
        if f.name not in overrides:
            continue
        val = overrides[f.name]
        cur = getattr(instance, f.name)
        if is_dataclass(cur):
            if val is None:
                updates[f.name] = None
            elif isinstance(val, dict):
                updates[f.name] = _apply_group_overrides(cur, val)
        elif cur is None and isinstance(val, dict):
            unwrapped = _unwrap_optional_type(hints.get(f.name, f.type))
            if is_dataclass(unwrapped) and isinstance(unwrapped, type):
                updates[f.name] = _apply_group_overrides(unwrapped(), val)
        elif isinstance(cur, tuple) and isinstance(val, list):
            updates[f.name] = tuple(val)
        elif isinstance(cur, float) and isinstance(val, int) and not isinstance(val, bool):
            updates[f.name] = float(val)
        else:
            updates[f.name] = val

    return replace(instance, **updates) if updates else instance


def _build_group_instance(
    factory: Callable[[], T],
    preset_key: str,
    overrides: dict[str, Any] | None,
) -> T:
    """Instantiate ``factory()`` layered with optional ``preset_key`` and ``overrides``."""
    instance = factory()
    if preset_key:
        preset_params = _load_component_preset_params(factory, preset_key)
        if preset_params:
            instance = _apply_group_overrides(instance, preset_params)
    if overrides:
        instance = _apply_group_overrides(instance, overrides)
    return instance


@overload
def group(
    factory: Callable[[], T],
    *,
    enabled: Literal[True] = True,
    preset: str | None = None,
    params: dict[str, Any] | None = None,
    label: str | None = None,
    desc: str | None = None,
    when: dict[str, Any] | None = None,
) -> T: ...


@overload
def group(
    factory: Callable[[], T],
    *,
    enabled: Literal[False],
    preset: str | None = None,
    params: dict[str, Any] | None = None,
    label: str | None = None,
    desc: str | None = None,
    when: dict[str, Any] | None = None,
) -> T | None: ...


def group(
    factory: Callable[[], T],
    *,
    enabled: bool = True,
    preset: str | None = None,
    params: dict[str, Any] | None = None,
    label: str | None = None,
    desc: str | None = None,
    when: dict[str, Any] | None = None,
) -> Any:
    """Define a nested parameter-group dataclass field with optional UI metadata.

    Pass ``enabled=False`` on a nullable group (``T | None``) to make the section
    optional and disabled by default (``None``). Optionally pass ``preset`` (a
    component preset key from the component's ``presets.json``) and/or ``params``
    (sparse per-model overrides) to customize a shared component's defaults.
    """
    meta: dict[str, Any] = {}
    if label is not None:
        meta["label"] = label
    if desc is not None:
        meta["description"] = desc
    if when is not None:
        meta["when"] = when
    clean_preset = preset.strip() if isinstance(preset, str) else ""
    if clean_preset == "default":
        clean_preset = ""
    if clean_preset:
        meta["component_preset"] = clean_preset
    if not enabled:
        return field(default=None, metadata=meta)
    if not clean_preset and not params:
        return field(default_factory=factory, metadata=meta)
    overrides = dict(params) if params else None
    return field(
        default_factory=lambda: _build_group_instance(factory, clean_preset, overrides),
        metadata=meta,
    )
