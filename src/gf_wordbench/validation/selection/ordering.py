"""Deterministic ordering and deduplication for selected GF source files."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
import os
from pathlib import Path, PurePosixPath
from typing import Generic, TypeVar

from gf_wordbench.kernel.statuses import ValidationMode

_ItemT = TypeVar("_ItemT")
_PathGetter = Callable[[_ItemT], Path]


@dataclass(frozen=True, slots=True)
class DiagnosticLimitResult(Generic[_ItemT]):
    selected: tuple[_ItemT, ...]
    overflow: tuple[_ItemT, ...]

    def __post_init__(self) -> None:
        selected = tuple(self.selected)
        overflow = tuple(self.overflow)

        selected_ids = {id(item) for item in selected}
        if any(id(item) in selected_ids for item in overflow):
            raise ValueError(
                "selected and overflow must not contain the same object"
            )

        object.__setattr__(self, "selected", selected)
        object.__setattr__(self, "overflow", overflow)


def resolved_identity_key(path: Path) -> str:
    normalized = _absolute_path(path, field_name="path")
    return os.path.normcase(str(normalized.resolve(strict=False)))


def project_relative_posix_path(
    path: Path,
    *,
    source_root: Path,
) -> PurePosixPath:
    normalized_path = _absolute_path(path, field_name="path").resolve(
        strict=False
    )
    normalized_root = _absolute_path(
        source_root,
        field_name="source_root",
    ).resolve(strict=False)

    try:
        relative = normalized_path.relative_to(normalized_root)
    except ValueError as exc:
        raise ValueError(
            f"path is outside source_root: {normalized_path}"
        ) from exc

    return PurePosixPath(*relative.parts)


def diagnostic_sort_key(
    path: Path,
    *,
    source_root: Path,
) -> tuple[str, str]:
    relative = project_relative_posix_path(
        path,
        source_root=source_root,
    ).as_posix()
    return relative.casefold(), relative


def deduplicate_preserving_order(
    items: Iterable[_ItemT],
    *,
    path_getter: _PathGetter[_ItemT],
) -> tuple[_ItemT, ...]:
    normalized = _item_tuple(items, field_name="items")
    getter = _callable(path_getter, field_name="path_getter")

    seen: set[str] = set()
    result: list[_ItemT] = []

    for item in normalized:
        key = resolved_identity_key(
            _item_path(item, path_getter=getter)
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(item)

    return tuple(result)


def ordered_union(
    first: Iterable[_ItemT],
    second: Iterable[_ItemT],
    *,
    path_getter: _PathGetter[_ItemT],
) -> tuple[_ItemT, ...]:
    getter = _callable(path_getter, field_name="path_getter")
    return deduplicate_preserving_order(
        (*_item_tuple(first, field_name="first"),
         *_item_tuple(second, field_name="second")),
        path_getter=getter,
    )


def order_quick(
    items: Iterable[_ItemT],
    *,
    path_getter: _PathGetter[_ItemT],
) -> tuple[_ItemT, ...]:
    ordered = deduplicate_preserving_order(
        items,
        path_getter=path_getter,
    )
    if len(ordered) != 1:
        raise ValueError(
            "quick mode requires exactly one selected target"
        )
    return ordered


def order_checkpoints(
    items: Iterable[_ItemT],
    *,
    path_getter: _PathGetter[_ItemT],
) -> tuple[_ItemT, ...]:
    return deduplicate_preserving_order(
        items,
        path_getter=path_getter,
    )


def order_release(
    checkpoints: Iterable[_ItemT],
    entrypoints: Iterable[_ItemT],
    *,
    path_getter: _PathGetter[_ItemT],
) -> tuple[_ItemT, ...]:
    return ordered_union(
        checkpoints,
        entrypoints,
        path_getter=path_getter,
    )


def order_diagnostic(
    items: Iterable[_ItemT],
    *,
    source_root: Path,
    path_getter: _PathGetter[_ItemT],
) -> tuple[_ItemT, ...]:
    getter = _callable(path_getter, field_name="path_getter")
    normalized_root = _absolute_path(
        source_root,
        field_name="source_root",
    )

    deduplicated = deduplicate_preserving_order(
        items,
        path_getter=getter,
    )
    return tuple(
        sorted(
            deduplicated,
            key=lambda item: diagnostic_sort_key(
                _item_path(item, path_getter=getter),
                source_root=normalized_root,
            ),
        )
    )


def apply_diagnostic_limit(
    items: Sequence[_ItemT],
    *,
    max_files: int,
) -> DiagnosticLimitResult[_ItemT]:
    normalized = _item_tuple(items, field_name="items")
    limit = _non_negative_integer(
        max_files,
        field_name="max_files",
    )

    if limit == 0 or len(normalized) <= limit:
        return DiagnosticLimitResult(
            selected=normalized,
            overflow=(),
        )

    return DiagnosticLimitResult(
        selected=normalized[:limit],
        overflow=normalized[limit:],
    )


def order_for_mode(
    *,
    mode: ValidationMode,
    quick: Iterable[_ItemT] = (),
    checkpoints: Iterable[_ItemT] = (),
    entrypoints: Iterable[_ItemT] = (),
    diagnostic: Iterable[_ItemT] = (),
    source_root: Path | None = None,
    max_files: int = 0,
    path_getter: _PathGetter[_ItemT],
) -> DiagnosticLimitResult[_ItemT]:
    if not isinstance(mode, ValidationMode):
        raise TypeError("mode must be a ValidationMode")

    getter = _callable(path_getter, field_name="path_getter")
    limit = _non_negative_integer(
        max_files,
        field_name="max_files",
    )

    if mode is ValidationMode.QUICK:
        ordered = order_quick(
            quick,
            path_getter=getter,
        )
        return DiagnosticLimitResult(
            selected=ordered,
            overflow=(),
        )

    if mode is ValidationMode.CHECKPOINT:
        if limit != 0:
            raise ValueError(
                "max_files must be 0 in checkpoint mode"
            )
        ordered = order_checkpoints(
            checkpoints,
            path_getter=getter,
        )
        return DiagnosticLimitResult(
            selected=ordered,
            overflow=(),
        )

    if mode is ValidationMode.RELEASE:
        if limit != 0:
            raise ValueError(
                "max_files must be 0 in release mode"
            )
        ordered = order_release(
            checkpoints,
            entrypoints,
            path_getter=getter,
        )
        return DiagnosticLimitResult(
            selected=ordered,
            overflow=(),
        )

    if mode is ValidationMode.DIAGNOSTIC:
        if source_root is None:
            raise ValueError(
                "source_root is required in diagnostic mode"
            )
        ordered = order_diagnostic(
            diagnostic,
            source_root=source_root,
            path_getter=getter,
        )
        return apply_diagnostic_limit(
            ordered,
            max_files=limit,
        )

    raise ValueError(f"unsupported validation mode: {mode!r}")


def order_excluded_explicit(
    items: Iterable[_ItemT],
    *,
    path_getter: _PathGetter[_ItemT],
) -> tuple[_ItemT, ...]:
    return deduplicate_preserving_order(
        items,
        path_getter=path_getter,
    )


def order_excluded_diagnostic(
    items: Iterable[_ItemT],
    *,
    source_root: Path,
    path_getter: _PathGetter[_ItemT],
) -> tuple[_ItemT, ...]:
    return order_diagnostic(
        items,
        source_root=source_root,
        path_getter=path_getter,
    )


def _item_path(
    item: _ItemT,
    *,
    path_getter: _PathGetter[_ItemT],
) -> Path:
    path = path_getter(item)
    if not isinstance(path, Path):
        raise TypeError(
            "path_getter must return pathlib.Path values"
        )
    return path


def _item_tuple(
    values: Iterable[_ItemT],
    *,
    field_name: str,
) -> tuple[_ItemT, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(
            f"{field_name} must be an iterable of items"
        )
    return tuple(values)


def _callable(
    value: object,
    *,
    field_name: str,
) -> Callable[..., object]:
    if not callable(value):
        raise TypeError(f"{field_name} must be callable")
    return value


def _absolute_path(
    value: object,
    *,
    field_name: str,
) -> Path:
    if not isinstance(value, Path):
        raise TypeError(
            f"{field_name} must be a pathlib.Path"
        )
    if "\x00" in str(value):
        raise ValueError(
            f"{field_name} must not contain NUL characters"
        )
    if not value.is_absolute():
        raise ValueError(
            f"{field_name} must be absolute"
        )
    return value


def _non_negative_integer(
    value: object,
    *,
    field_name: str,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(
            f"{field_name} must be an integer"
        )
    if value < 0:
        raise ValueError(
            f"{field_name} must be non-negative"
        )
    return value


__all__ = (
    "DiagnosticLimitResult",
    "apply_diagnostic_limit",
    "deduplicate_preserving_order",
    "diagnostic_sort_key",
    "order_checkpoints",
    "order_diagnostic",
    "order_excluded_diagnostic",
    "order_excluded_explicit",
    "order_for_mode",
    "order_quick",
    "order_release",
    "ordered_union",
    "project_relative_posix_path",
    "resolved_identity_key",
)
