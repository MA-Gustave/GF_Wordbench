from __future__ import annotations

from collections.abc import Mapping
from os import PathLike
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, cast

from gf_wordbench.infrastructure.json_io import JsonObject, read_json, write_json
from gf_wordbench.reporting.schemas.summary_v1 import validate_summary_document
from gf_wordbench.reporting.summary.projection import build_summary_document

if TYPE_CHECKING:
    from gf_wordbench.runs.models.results import RunResult

__all__ = [
    "SUMMARY_FILENAME",
    "SummaryJsonWriter",
    "write_summary_document",
    "write_summary_json",
]

SUMMARY_FILENAME: Final[str] = "summary.json"


def _as_json_object(document: Mapping[str, Any]) -> JsonObject:
    if not isinstance(document, dict):
        document = dict(document)
    return cast(JsonObject, document)


def _summary_path(run_result: RunResult) -> Path:
    run_paths = getattr(run_result, "run_paths", None)
    if run_paths is None:
        raise TypeError("run_result must expose run_paths")
    value = getattr(run_paths, "summary_json_path", None)
    if value is None:
        raise TypeError("run_result.run_paths must expose summary_json_path")
    if not isinstance(value, (str, PathLike)):
        raise TypeError("summary_json_path must be path-like")
    path = Path(value)
    if path.name != SUMMARY_FILENAME:
        raise ValueError(f"summary_json_path must end with {SUMMARY_FILENAME}")
    return path


def write_summary_document(
    destination: str | PathLike[str],
    document: Mapping[str, Any],
) -> Path:
    path = Path(destination)
    if path.name != SUMMARY_FILENAME:
        raise ValueError(f"destination must end with {SUMMARY_FILENAME}")
    canonical = _as_json_object(document)
    validate_summary_document(canonical)
    written = write_json(path, canonical)
    persisted = read_json(written)
    validate_summary_document(persisted)
    if persisted != canonical:
        raise RuntimeError("persisted summary differs from the canonical document")
    return written


def write_summary_json(run_result: RunResult) -> Path:
    destination = _summary_path(run_result)
    document = _as_json_object(build_summary_document(run_result))
    return write_summary_document(destination, document)


class SummaryJsonWriter:
    __slots__ = ()

    def write(self, run_result: RunResult) -> Path:
        return write_summary_json(run_result)

    def __call__(self, run_result: RunResult) -> Path:
        return self.write(run_result)
