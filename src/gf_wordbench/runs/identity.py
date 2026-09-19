"""Canonical run-identity construction and parsing."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Final

from gf_wordbench.kernel.ids import RunId, validate_run_id

RUN_DIRECTORY_PREFIX: Final[str] = "run_"
RUN_ID_TIMESTAMP_FORMAT: Final[str] = "%Y%m%d_%H%M%S"
BASE_COLLISION_INDEX: Final[int] = 1
FIRST_SUFFIXED_COLLISION_INDEX: Final[int] = 2


def create_run_id(
    timestamp: datetime,
    *,
    collision_index: int = BASE_COLLISION_INDEX,
) -> RunId:
    """Create a canonical UTC run identifier."""

    normalized = _require_aware_datetime(timestamp)
    index = _require_collision_index(collision_index)
    base = normalized.astimezone(UTC).strftime(RUN_ID_TIMESTAMP_FORMAT)

    if index == BASE_COLLISION_INDEX:
        return validate_run_id(base)

    return validate_run_id(f"{base}_{index:02d}")


def create_collision_run_id(
    base_run_id: RunId | str,
    collision_index: int,
) -> RunId:
    """Create a collision-suffixed identifier from a canonical base ID."""

    validated = validate_run_id(base_run_id)
    index = _require_collision_index(collision_index)

    if run_id_collision_index(validated) != BASE_COLLISION_INDEX:
        raise ValueError("base_run_id must not already contain a collision suffix")
    if index == BASE_COLLISION_INDEX:
        return validated

    return validate_run_id(f"{validated}_{index:02d}")


def iter_run_id_candidates(timestamp: datetime) -> Iterator[RunId]:
    """Yield deterministic run-ID candidates for atomic allocation."""

    normalized = _require_aware_datetime(timestamp).astimezone(UTC)
    collision_index = BASE_COLLISION_INDEX

    while True:
        yield create_run_id(
            normalized,
            collision_index=collision_index,
        )
        collision_index += 1


def run_directory_name(run_id: RunId | str) -> str:
    """Return the canonical directory name for a run identifier."""

    return f"{RUN_DIRECTORY_PREFIX}{validate_run_id(run_id)}"


def parse_run_directory_name(value: object) -> RunId:
    """Parse an exact canonical run-directory basename."""

    if not isinstance(value, str):
        raise TypeError(f"run directory name must be a string, got {type(value).__name__}")
    if not value:
        raise ValueError("run directory name must not be empty")
    if "/" in value or "\\" in value:
        raise ValueError("run directory name must be a basename")
    if not value.startswith(RUN_DIRECTORY_PREFIX):
        raise ValueError(f"run directory name must begin with {RUN_DIRECTORY_PREFIX!r}")

    run_id_text = value[len(RUN_DIRECTORY_PREFIX) :]
    if not run_id_text:
        raise ValueError("run directory name must contain a run ID")

    return validate_run_id(
        run_id_text,
        field="run directory run ID",
    )


def run_id_timestamp(run_id: RunId | str) -> datetime:
    """Return the timezone-aware UTC timestamp encoded by a run ID."""

    validated = validate_run_id(run_id)
    timestamp_text = str(validated)[:15]
    parsed = datetime.strptime(
        timestamp_text,
        RUN_ID_TIMESTAMP_FORMAT,
    )
    return parsed.replace(tzinfo=UTC)


def run_id_collision_index(run_id: RunId | str) -> int:
    """Return one for a base ID or the encoded collision index."""

    validated = str(validate_run_id(run_id))
    suffix = validated[15:]

    if not suffix:
        return BASE_COLLISION_INDEX

    return int(suffix[1:])


def is_run_directory_name(value: object) -> bool:
    """Return whether a value is an exact canonical run-directory basename."""

    try:
        parse_run_directory_name(value)
    except (TypeError, ValueError):
        return False
    return True


def _require_aware_datetime(value: object) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"timestamp must be a datetime, got {type(value).__name__}")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return value


def _require_collision_index(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("collision_index must be an integer")
    if value < BASE_COLLISION_INDEX:
        raise ValueError("collision_index must be at least 1")
    return value


__all__ = (
    "BASE_COLLISION_INDEX",
    "FIRST_SUFFIXED_COLLISION_INDEX",
    "RUN_DIRECTORY_PREFIX",
    "RUN_ID_TIMESTAMP_FORMAT",
    "create_collision_run_id",
    "create_run_id",
    "is_run_directory_name",
    "iter_run_id_candidates",
    "parse_run_directory_name",
    "run_directory_name",
    "run_id_collision_index",
    "run_id_timestamp",
)
