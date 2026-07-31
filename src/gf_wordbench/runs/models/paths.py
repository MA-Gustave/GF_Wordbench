"""Immutable authoritative path registry for one GF Wordbench run."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Final

from gf_wordbench.kernel.errors import ContractViolationError
from gf_wordbench.kernel.ids import validate_run_id
from gf_wordbench.kernel.paths import (
    ContainmentMode,
    PathInput,
    normalize_environment_path,
    relative_portable_path,
    require_lexical_containment,
)

_RUN_DIRECTORY_PREFIX: Final[str] = "run_"

_SUMMARY_JSON: Final[str] = "summary.json"
_SUMMARY_MD: Final[str] = "summary.md"
_AI_READY_MD: Final[str] = "AI_READY.md"
_TOP_ERRORS_TXT: Final[str] = "top_errors.txt"
_MANIFEST_JSON: Final[str] = "manifest.json"

_DETAILS_DIRECTORY: Final[str] = "details"
_RAW_DIRECTORY: Final[str] = "raw"
_MASTER_LOG: Final[str] = "master.log"
_ALL_SCAN_LOGS: Final[str] = "ALL_SCAN_LOGS.TXT"
_ALL_LOGS: Final[str] = "ALL_LOGS.TXT"
_RAW_COMPILE_DIRECTORY: Final[str] = "compile"
_RAW_SCAN_DIRECTORY: Final[str] = "scan"
_RAW_SCENARIOS_DIRECTORY: Final[str] = "scenarios"

_ARTIFACTS_DIRECTORY: Final[str] = "artifacts"
_GFO_DIRECTORY: Final[str] = "gfo"
_OUT_DIRECTORY: Final[str] = "out"
_PGF_DIRECTORY: Final[str] = "pgf"


@dataclass(frozen=True, slots=True)
class RunPaths:
    """Absolute canonical paths owned by one immutable run identity."""

    run_id: str
    run_dir: Path

    summary_json: Path
    summary_md: Path
    ai_ready_md: Path
    top_errors_txt: Path
    manifest_json: Path

    details_dir: Path

    raw_dir: Path
    master_log: Path
    all_scan_logs: Path
    all_logs: Path
    raw_compile_dir: Path
    raw_scan_dir: Path
    raw_scenarios_dir: Path

    artifacts_dir: Path
    gfo_dir: Path
    out_dir: Path
    pgf_dir: Path

    def __post_init__(self) -> None:
        run_id = str(validate_run_id(self.run_id, field="run ID"))
        run_dir = normalize_environment_path(
            self.run_dir,
            role="run directory",
        )

        expected_name = f"{_RUN_DIRECTORY_PREFIX}{run_id}"
        if run_dir.name != expected_name:
            raise ContractViolationError(
                "run directory name must match the canonical run identity: "
                f"expected {expected_name!r}, got {run_dir.name!r}"
            )

        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(self, "run_dir", run_dir)

        expected_paths = {
            "summary_json": run_dir / _SUMMARY_JSON,
            "summary_md": run_dir / _SUMMARY_MD,
            "ai_ready_md": run_dir / _AI_READY_MD,
            "top_errors_txt": run_dir / _TOP_ERRORS_TXT,
            "manifest_json": run_dir / _MANIFEST_JSON,
            "details_dir": run_dir / _DETAILS_DIRECTORY,
            "raw_dir": run_dir / _RAW_DIRECTORY,
            "master_log": run_dir / _RAW_DIRECTORY / _MASTER_LOG,
            "all_scan_logs": run_dir / _RAW_DIRECTORY / _ALL_SCAN_LOGS,
            "all_logs": run_dir / _RAW_DIRECTORY / _ALL_LOGS,
            "raw_compile_dir": (
                run_dir / _RAW_DIRECTORY / _RAW_COMPILE_DIRECTORY
            ),
            "raw_scan_dir": run_dir / _RAW_DIRECTORY / _RAW_SCAN_DIRECTORY,
            "raw_scenarios_dir": (
                run_dir / _RAW_DIRECTORY / _RAW_SCENARIOS_DIRECTORY
            ),
            "artifacts_dir": run_dir / _ARTIFACTS_DIRECTORY,
            "gfo_dir": run_dir / _ARTIFACTS_DIRECTORY / _GFO_DIRECTORY,
            "out_dir": run_dir / _ARTIFACTS_DIRECTORY / _OUT_DIRECTORY,
            "pgf_dir": run_dir / _ARTIFACTS_DIRECTORY / _PGF_DIRECTORY,
        }

        normalized_paths: dict[str, Path] = {}
        for field_name, expected in expected_paths.items():
            candidate = normalize_environment_path(
                getattr(self, field_name),
                role=field_name.replace("_", " "),
            )
            candidate = require_lexical_containment(
                run_dir,
                candidate,
                role=field_name.replace("_", " "),
                mode=ContainmentMode.STRICTLY_INSIDE,
            )
            if candidate.as_posix() != expected.as_posix():
                raise ContractViolationError(
                    f"{field_name} must use its canonical run-relative location: "
                    f"expected {expected!s}, got {candidate!s}"
                )
            normalized_paths[field_name] = candidate

        if len(set(normalized_paths.values())) != len(normalized_paths):
            raise ContractViolationError(
                "canonical run-owned paths must be pairwise distinct"
            )

        for field_name, candidate in normalized_paths.items():
            object.__setattr__(self, field_name, candidate)

    @property
    def report_files(self) -> tuple[Path, ...]:
        """Return canonical top-level report and manifest paths."""

        return (
            self.summary_json,
            self.summary_md,
            self.ai_ready_md,
            self.top_errors_txt,
            self.manifest_json,
        )

    @property
    def log_files(self) -> tuple[Path, ...]:
        """Return canonical aggregate run-log paths."""

        return (
            self.master_log,
            self.all_scan_logs,
            self.all_logs,
        )

    @property
    def standard_directories(self) -> tuple[Path, ...]:
        """Return standard run directories in deterministic creation order."""

        return (
            self.details_dir,
            self.raw_dir,
            self.raw_compile_dir,
            self.raw_scan_dir,
            self.raw_scenarios_dir,
            self.artifacts_dir,
            self.gfo_dir,
            self.out_dir,
            self.pgf_dir,
        )

    @property
    def owned_paths(self) -> tuple[Path, ...]:
        """Return every canonical path owned by the run."""

        return (
            self.run_dir,
            *self.report_files,
            self.details_dir,
            self.raw_dir,
            *self.log_files,
            self.raw_compile_dir,
            self.raw_scan_dir,
            self.raw_scenarios_dir,
            self.artifacts_dir,
            self.gfo_dir,
            self.out_dir,
            self.pgf_dir,
        )

    def require_owned_path(
        self,
        value: PathInput,
        *,
        role: str = "run-owned path",
        allow_run_dir: bool = False,
    ) -> Path:
        """Normalize a path and require lexical containment in this run."""

        mode = (
            ContainmentMode.INSIDE_OR_EQUAL
            if allow_run_dir
            else ContainmentMode.STRICTLY_INSIDE
        )
        return require_lexical_containment(
            self.run_dir,
            value,
            role=role,
            mode=mode,
        )

    def relative_path(
        self,
        value: PathInput,
        *,
        role: str = "run-owned path",
        allow_run_dir: bool = False,
    ) -> PurePosixPath:
        """Return the canonical run-relative portable form of a path."""

        mode = (
            ContainmentMode.INSIDE_OR_EQUAL
            if allow_run_dir
            else ContainmentMode.STRICTLY_INSIDE
        )
        return relative_portable_path(
            self.run_dir,
            value,
            role=role,
            mode=mode,
        )


__all__ = ("RunPaths",)
