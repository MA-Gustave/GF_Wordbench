"""Explicit, reviewed, atomic scenario-gold updates."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from difflib import unified_diff
from enum import StrEnum, unique
import hashlib
import json
from pathlib import Path
import re
from types import MappingProxyType
from typing import Final, Protocol, TypeAlias

from gf_wordbench.infrastructure.atomic_io import (
    atomic_write_bytes,
    atomic_write_text,
)
from gf_wordbench.kernel.ids import (
    RunId,
    ScenarioId,
    validate_run_id,
    validate_scenario_id,
)
from gf_wordbench.kernel.paths import (
    ContainmentMode,
    require_lexical_containment,
)

GOLD_SCHEMA_HEADER: Final[str] = "# GF_WORDBENCH_GOLD 1.0"
OUTPUT_SCHEMA_HEADER: Final[str] = "# GF_WORDBENCH_OUTPUT 1.0"
SCENARIO_HEADER_PREFIX: Final[str] = "# scenario_id: "
NORMALIZATION_HEADER_PREFIX: Final[str] = "# normalization_version: "
GOLD_DIRECTORY_PARTS: Final[tuple[str, ...]] = (
    "validation",
    "gold",
)
GOLD_SUFFIX: Final[str] = ".gold"
UTF8_ENCODING: Final[str] = "utf-8"
SHA256_HEX_LENGTH: Final[int] = 64
MAX_DIFF_CHARS: Final[int] = 1_000_000
MAX_RECORD_TEXT_CHARS: Final[int] = 8_000

_SECTION_BEGIN_RE: Final[re.Pattern[str]] = re.compile(
    r"^--- BEGIN (?P<section>[a-z][a-z0-9]*(?:-[a-z0-9]+)*) ---$"
)
_SECTION_END_RE: Final[re.Pattern[str]] = re.compile(
    r"^--- END (?P<section>[a-z][a-z0-9]*(?:-[a-z0-9]+)*) ---$"
)
_VERSION_RE: Final[re.Pattern[str]] = re.compile(r"^[0-9]+(?:\.[0-9]+){1,3}$")


@unique
class GoldUpdateStatus(StrEnum):
    READY = "ready"
    UNCHANGED = "unchanged"
    DECLINED = "declined"
    REFUSED = "refused"
    UPDATED = "updated"


@unique
class GoldUpdateRefusalCode(StrEnum):
    INVALID_OUTPUT_SCHEMA = "invalid_output_schema"
    SCENARIO_MISMATCH = "scenario_mismatch"
    NORMALIZATION_MISMATCH = "normalization_mismatch"
    MARKERS_INVALID = "markers_invalid"
    NORMALIZATION_FAILED = "normalization_failed"
    OUTPUT_TRUNCATED = "output_truncated"
    OUTPUT_INCOMPLETE = "output_incomplete"
    OUTPUT_NOT_MEANINGFUL = "output_not_meaningful"
    COMPATIBILITY_UNKNOWN = "compatibility_unknown"
    NONDETERMINISTIC = "nondeterministic"
    DIFF_NOT_REVIEWED = "diff_not_reviewed"
    INTENT_NOT_RECORDED = "intent_not_recorded"
    REVIEWER_NOT_RECORDED = "reviewer_not_recorded"
    DECISION_NOT_RECORDED = "decision_not_recorded"
    PATH_UNSAFE = "path_unsafe"
    PREVIOUS_HASH_MISMATCH = "previous_hash_mismatch"


@dataclass(frozen=True, slots=True)
class GoldDocument:
    scenario_id: ScenarioId
    normalization_version: str
    sections: tuple[str, ...]
    text: str

    def __post_init__(self) -> None:
        scenario_id = validate_scenario_id(self.scenario_id)
        normalization_version = _validate_version(
            self.normalization_version,
            field_name="normalization_version",
        )
        sections = _section_tuple(self.sections)
        text = _canonical_text(
            self.text,
            field_name="text",
        )

        object.__setattr__(self, "scenario_id", scenario_id)
        object.__setattr__(
            self,
            "normalization_version",
            normalization_version,
        )
        object.__setattr__(self, "sections", sections)
        object.__setattr__(self, "text", text)


@dataclass(frozen=True, slots=True)
class GoldUpdateRefusal:
    code: GoldUpdateRefusalCode
    message: str

    def __post_init__(self) -> None:
        if not isinstance(self.code, GoldUpdateRefusalCode):
            raise TypeError("code must be a GoldUpdateRefusalCode")
        message = _required_text(
            self.message,
            field_name="message",
        )
        object.__setattr__(self, "message", message)


@dataclass(frozen=True, slots=True)
class GoldUpdateRequest:
    project_root: Path
    scenario_id: ScenarioId
    source_run_id: RunId
    normalized_output_text: str
    normalization_version: str
    reviewer: str
    rationale: str
    decision_reference: str
    raw_stdout_path: Path
    raw_stderr_path: Path
    normalized_output_path: Path
    diff_evidence_path: Path | None = None
    confirmed: bool = False
    diff_reviewed: bool = False
    markers_valid: bool = True
    normalization_succeeded: bool = True
    output_truncated: bool = False
    output_complete: bool = True
    compatibility_verified: bool = True
    deterministic: bool = True
    allow_empty: bool = False
    expected_previous_sha256: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        project_root = _absolute_path(
            self.project_root,
            field_name="project_root",
        )
        scenario_id = validate_scenario_id(self.scenario_id)
        source_run_id = validate_run_id(self.source_run_id)
        normalized_output_text = _canonical_text(
            self.normalized_output_text,
            field_name="normalized_output_text",
        )
        normalization_version = _validate_version(
            self.normalization_version,
            field_name="normalization_version",
        )
        reviewer = _required_text(
            self.reviewer,
            field_name="reviewer",
        )
        rationale = _required_text(
            self.rationale,
            field_name="rationale",
        )
        decision_reference = _required_text(
            self.decision_reference,
            field_name="decision_reference",
        )
        raw_stdout_path = _absolute_path(
            self.raw_stdout_path,
            field_name="raw_stdout_path",
        )
        raw_stderr_path = _absolute_path(
            self.raw_stderr_path,
            field_name="raw_stderr_path",
        )
        normalized_output_path = _absolute_path(
            self.normalized_output_path,
            field_name="normalized_output_path",
        )
        diff_evidence_path = _optional_absolute_path(
            self.diff_evidence_path,
            field_name="diff_evidence_path",
        )

        for field_name in (
            "confirmed",
            "diff_reviewed",
            "markers_valid",
            "normalization_succeeded",
            "output_truncated",
            "output_complete",
            "compatibility_verified",
            "deterministic",
            "allow_empty",
        ):
            if not isinstance(getattr(self, field_name), bool):
                raise TypeError(f"{field_name} must be a bool")

        expected_previous_sha256 = _optional_sha256(
            self.expected_previous_sha256,
            field_name="expected_previous_sha256",
        )
        metadata = _string_mapping(
            self.metadata,
            field_name="metadata",
        )

        object.__setattr__(self, "project_root", project_root)
        object.__setattr__(self, "scenario_id", scenario_id)
        object.__setattr__(self, "source_run_id", source_run_id)
        object.__setattr__(
            self,
            "normalized_output_text",
            normalized_output_text,
        )
        object.__setattr__(
            self,
            "normalization_version",
            normalization_version,
        )
        object.__setattr__(self, "reviewer", reviewer)
        object.__setattr__(self, "rationale", rationale)
        object.__setattr__(
            self,
            "decision_reference",
            decision_reference,
        )
        object.__setattr__(
            self,
            "raw_stdout_path",
            raw_stdout_path,
        )
        object.__setattr__(
            self,
            "raw_stderr_path",
            raw_stderr_path,
        )
        object.__setattr__(
            self,
            "normalized_output_path",
            normalized_output_path,
        )
        object.__setattr__(
            self,
            "diff_evidence_path",
            diff_evidence_path,
        )
        object.__setattr__(
            self,
            "expected_previous_sha256",
            expected_previous_sha256,
        )
        object.__setattr__(self, "metadata", metadata)

    @property
    def gold_root(self) -> Path:
        return self.project_root.joinpath(*GOLD_DIRECTORY_PARTS)

    @property
    def gold_path(self) -> Path:
        return self.gold_root / f"{self.scenario_id}{GOLD_SUFFIX}"


@dataclass(frozen=True, slots=True)
class GoldUpdatePlan:
    request: GoldUpdateRequest
    status: GoldUpdateStatus
    gold_path: Path
    candidate: GoldDocument | None
    previous_exists: bool
    previous_sha256: str | None
    candidate_sha256: str | None
    diff_text: str
    refusals: tuple[GoldUpdateRefusal, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.request, GoldUpdateRequest):
            raise TypeError("request must be a GoldUpdateRequest")
        if not isinstance(self.status, GoldUpdateStatus):
            raise TypeError("status must be a GoldUpdateStatus")
        gold_path = _absolute_path(
            self.gold_path,
            field_name="gold_path",
        )
        if self.candidate is not None and not isinstance(self.candidate, GoldDocument):
            raise TypeError("candidate must be a GoldDocument or None")
        if not isinstance(self.previous_exists, bool):
            raise TypeError("previous_exists must be a bool")
        previous_sha256 = _optional_sha256(
            self.previous_sha256,
            field_name="previous_sha256",
        )
        candidate_sha256 = _optional_sha256(
            self.candidate_sha256,
            field_name="candidate_sha256",
        )
        if not isinstance(self.diff_text, str):
            raise TypeError("diff_text must be a string")
        refusals = tuple(self.refusals)
        if not all(isinstance(item, GoldUpdateRefusal) for item in refusals):
            raise TypeError("refusals must contain GoldUpdateRefusal values")

        if self.status is GoldUpdateStatus.REFUSED and not refusals:
            raise ValueError("refused plan requires at least one refusal")
        if self.status is not GoldUpdateStatus.REFUSED and refusals:
            raise ValueError("non-refused plan cannot contain refusals")
        if (
            self.status
            in {
                GoldUpdateStatus.READY,
                GoldUpdateStatus.UNCHANGED,
            }
            and self.candidate is None
        ):
            raise ValueError("ready or unchanged plan requires a candidate")

        object.__setattr__(self, "gold_path", gold_path)
        object.__setattr__(
            self,
            "previous_sha256",
            previous_sha256,
        )
        object.__setattr__(
            self,
            "candidate_sha256",
            candidate_sha256,
        )
        object.__setattr__(self, "refusals", refusals)

    @property
    def changed(self) -> bool:
        return self.status is GoldUpdateStatus.READY

    @property
    def writable(self) -> bool:
        return (
            self.status is GoldUpdateStatus.READY
            and self.request.confirmed
            and self.request.diff_reviewed
        )


@dataclass(frozen=True, slots=True)
class GoldUpdateRecord:
    scenario_id: ScenarioId
    source_run_id: RunId
    gold_path: Path
    previous_sha256: str | None
    new_sha256: str
    normalization_version: str
    reviewer: str
    rationale: str
    decision_reference: str
    raw_stdout_path: Path
    raw_stderr_path: Path
    normalized_output_path: Path
    diff_evidence_path: Path | None
    updated_at: datetime
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        scenario_id = validate_scenario_id(self.scenario_id)
        source_run_id = validate_run_id(self.source_run_id)
        gold_path = _absolute_path(
            self.gold_path,
            field_name="gold_path",
        )
        previous_sha256 = _optional_sha256(
            self.previous_sha256,
            field_name="previous_sha256",
        )
        new_sha256 = _required_sha256(
            self.new_sha256,
            field_name="new_sha256",
        )
        normalization_version = _validate_version(
            self.normalization_version,
            field_name="normalization_version",
        )
        reviewer = _required_text(
            self.reviewer,
            field_name="reviewer",
        )
        rationale = _bounded_text(
            self.rationale,
            field_name="rationale",
        )
        decision_reference = _bounded_text(
            self.decision_reference,
            field_name="decision_reference",
        )
        raw_stdout_path = _absolute_path(
            self.raw_stdout_path,
            field_name="raw_stdout_path",
        )
        raw_stderr_path = _absolute_path(
            self.raw_stderr_path,
            field_name="raw_stderr_path",
        )
        normalized_output_path = _absolute_path(
            self.normalized_output_path,
            field_name="normalized_output_path",
        )
        diff_evidence_path = _optional_absolute_path(
            self.diff_evidence_path,
            field_name="diff_evidence_path",
        )
        updated_at = _utc_datetime(
            self.updated_at,
            field_name="updated_at",
        )
        metadata = _string_mapping(
            self.metadata,
            field_name="metadata",
        )

        object.__setattr__(self, "scenario_id", scenario_id)
        object.__setattr__(self, "source_run_id", source_run_id)
        object.__setattr__(self, "gold_path", gold_path)
        object.__setattr__(
            self,
            "previous_sha256",
            previous_sha256,
        )
        object.__setattr__(self, "new_sha256", new_sha256)
        object.__setattr__(
            self,
            "normalization_version",
            normalization_version,
        )
        object.__setattr__(self, "reviewer", reviewer)
        object.__setattr__(self, "rationale", rationale)
        object.__setattr__(
            self,
            "decision_reference",
            decision_reference,
        )
        object.__setattr__(
            self,
            "raw_stdout_path",
            raw_stdout_path,
        )
        object.__setattr__(
            self,
            "raw_stderr_path",
            raw_stderr_path,
        )
        object.__setattr__(
            self,
            "normalized_output_path",
            normalized_output_path,
        )
        object.__setattr__(
            self,
            "diff_evidence_path",
            diff_evidence_path,
        )
        object.__setattr__(self, "updated_at", updated_at)
        object.__setattr__(self, "metadata", metadata)

    def to_mapping(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "scenario_id": str(self.scenario_id),
                "source_run_id": str(self.source_run_id),
                "gold_path": str(self.gold_path),
                "previous_sha256": self.previous_sha256,
                "new_sha256": self.new_sha256,
                "normalization_version": self.normalization_version,
                "reviewer": self.reviewer,
                "rationale": self.rationale,
                "decision_reference": self.decision_reference,
                "raw_stdout_path": str(self.raw_stdout_path),
                "raw_stderr_path": str(self.raw_stderr_path),
                "normalized_output_path": str(self.normalized_output_path),
                "diff_evidence_path": (
                    str(self.diff_evidence_path) if self.diff_evidence_path is not None else None
                ),
                "updated_at": self.updated_at.isoformat().replace(
                    "+00:00",
                    "Z",
                ),
                "metadata": dict(self.metadata),
            }
        )

    def to_json(self) -> str:
        return (
            json.dumps(
                self.to_mapping(),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        )


@dataclass(frozen=True, slots=True)
class GoldUpdateResult:
    status: GoldUpdateStatus
    plan: GoldUpdatePlan
    record: GoldUpdateRecord | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.status, GoldUpdateStatus):
            raise TypeError("status must be a GoldUpdateStatus")
        if not isinstance(self.plan, GoldUpdatePlan):
            raise TypeError("plan must be a GoldUpdatePlan")
        if self.record is not None and not isinstance(self.record, GoldUpdateRecord):
            raise TypeError("record must be a GoldUpdateRecord or None")
        if self.status is GoldUpdateStatus.UPDATED and self.record is None:
            raise ValueError("updated result requires an update record")
        if self.status is not GoldUpdateStatus.UPDATED and self.record is not None:
            raise ValueError("only an updated result may contain a record")


class GoldUpdateError(RuntimeError):
    pass


class GoldUpdateIntegrityError(GoldUpdateError):
    pass


class GoldUpdateConcurrentChangeError(GoldUpdateError):
    pass


class GoldUpdateWriter(Protocol):
    def __call__(
        self,
        destination: Path,
        text: str,
        *,
        encoding: str,
        newline: str | None,
        create_parents: bool,
        root: Path,
        role: str,
        sync: bool,
        preserve_existing_mode: bool,
    ) -> Path: ...


TextReader: TypeAlias = Callable[[Path], str]
BytesReader: TypeAlias = Callable[[Path], bytes]
Clock: TypeAlias = Callable[[], datetime]


def parse_normalized_output_document(
    text: str,
    *,
    expected_scenario_id: ScenarioId | str,
    expected_normalization_version: str,
) -> GoldDocument:
    canonical = _canonical_text(
        text,
        field_name="normalized output",
    )
    scenario_id = validate_scenario_id(
        expected_scenario_id,
        field="expected scenario ID",
    )
    normalization_version = _validate_version(
        expected_normalization_version,
        field_name="expected_normalization_version",
    )
    lines = canonical.splitlines()

    if len(lines) < 3:
        raise ValueError("normalized output is missing the canonical header")
    if lines[0] != OUTPUT_SCHEMA_HEADER:
        raise ValueError(f"normalized output must begin with {OUTPUT_SCHEMA_HEADER!r}")

    actual_scenario = _header_value(
        lines[1],
        prefix=SCENARIO_HEADER_PREFIX,
        field_name="scenario_id",
    )
    actual_scenario_id = validate_scenario_id(
        actual_scenario,
        field="normalized output scenario ID",
    )
    if actual_scenario_id != scenario_id:
        raise ValueError(
            "normalized output scenario ID does not match "
            f"the selected scenario: {actual_scenario_id!r} "
            f"!= {scenario_id!r}"
        )

    actual_normalization = _header_value(
        lines[2],
        prefix=NORMALIZATION_HEADER_PREFIX,
        field_name="normalization_version",
    )
    actual_normalization = _validate_version(
        actual_normalization,
        field_name="normalized output normalization version",
    )
    if actual_normalization != normalization_version:
        raise ValueError(
            "normalized output normalization version does not "
            f"match the selected version: {actual_normalization!r} "
            f"!= {normalization_version!r}"
        )

    sections = _validate_sections(lines[3:])
    gold_text = "\n".join(
        (
            GOLD_SCHEMA_HEADER,
            f"{SCENARIO_HEADER_PREFIX}{scenario_id}",
            (f"{NORMALIZATION_HEADER_PREFIX}{normalization_version}"),
            *lines[3:],
        )
    )
    gold_text = _canonical_text(
        gold_text,
        field_name="gold text",
    )

    return GoldDocument(
        scenario_id=scenario_id,
        normalization_version=normalization_version,
        sections=sections,
        text=gold_text,
    )


def parse_gold_document(
    text: str,
    *,
    expected_scenario_id: ScenarioId | str | None = None,
    expected_normalization_version: str | None = None,
) -> GoldDocument:
    canonical = _canonical_text(text, field_name="gold text")
    lines = canonical.splitlines()

    if len(lines) < 3:
        raise ValueError("gold document is missing the canonical header")
    if lines[0] != GOLD_SCHEMA_HEADER:
        raise ValueError(f"gold document must begin with {GOLD_SCHEMA_HEADER!r}")

    scenario_text = _header_value(
        lines[1],
        prefix=SCENARIO_HEADER_PREFIX,
        field_name="scenario_id",
    )
    scenario_id = validate_scenario_id(
        scenario_text,
        field="gold scenario ID",
    )
    normalization_version = _validate_version(
        _header_value(
            lines[2],
            prefix=NORMALIZATION_HEADER_PREFIX,
            field_name="normalization_version",
        ),
        field_name="gold normalization version",
    )
    sections = _validate_sections(lines[3:])

    if expected_scenario_id is not None:
        expected_id = validate_scenario_id(
            expected_scenario_id,
            field="expected scenario ID",
        )
        if scenario_id != expected_id:
            raise ValueError(
                "gold scenario ID does not match the expected "
                f"scenario: {scenario_id!r} != {expected_id!r}"
            )

    if expected_normalization_version is not None:
        expected_version = _validate_version(
            expected_normalization_version,
            field_name="expected_normalization_version",
        )
        if normalization_version != expected_version:
            raise ValueError(
                "gold normalization version does not match the "
                f"expected version: {normalization_version!r} "
                f"!= {expected_version!r}"
            )

    return GoldDocument(
        scenario_id=scenario_id,
        normalization_version=normalization_version,
        sections=sections,
        text=canonical,
    )


def prepare_gold_update(
    request: GoldUpdateRequest,
    *,
    read_bytes: BytesReader = Path.read_bytes,
) -> GoldUpdatePlan:
    if not isinstance(request, GoldUpdateRequest):
        raise TypeError("request must be a GoldUpdateRequest")
    if not callable(read_bytes):
        raise TypeError("read_bytes must be callable")

    gold_path = _validated_gold_path(request)
    refusals = _request_refusals(request)

    candidate: GoldDocument | None = None
    try:
        candidate = parse_normalized_output_document(
            request.normalized_output_text,
            expected_scenario_id=request.scenario_id,
            expected_normalization_version=(request.normalization_version),
        )
    except (TypeError, ValueError) as exc:
        refusals.append(
            GoldUpdateRefusal(
                code=GoldUpdateRefusalCode.INVALID_OUTPUT_SCHEMA,
                message=str(exc),
            )
        )

    previous_bytes: bytes | None
    try:
        previous_bytes = read_bytes(gold_path)
    except FileNotFoundError:
        previous_bytes = None
    except OSError as exc:
        raise GoldUpdateError(f"unable to read existing gold file: {exc}") from exc

    previous_exists = previous_bytes is not None
    previous_sha256 = _sha256(previous_bytes) if previous_bytes is not None else None

    if (
        request.expected_previous_sha256 is not None
        and previous_sha256 != request.expected_previous_sha256
    ):
        refusals.append(
            GoldUpdateRefusal(
                code=(GoldUpdateRefusalCode.PREVIOUS_HASH_MISMATCH),
                message=("existing gold SHA-256 does not match the reviewed previous hash"),
            )
        )

    candidate_bytes = candidate.text.encode(UTF8_ENCODING) if candidate is not None else None
    candidate_sha256 = _sha256(candidate_bytes) if candidate_bytes is not None else None

    old_text = ""
    if previous_bytes is not None:
        try:
            old_text = previous_bytes.decode(UTF8_ENCODING)
        except UnicodeDecodeError:
            refusals.append(
                GoldUpdateRefusal(
                    code=(GoldUpdateRefusalCode.INVALID_OUTPUT_SCHEMA),
                    message=("existing gold file is not valid UTF-8"),
                )
            )
            old_text = previous_bytes.decode(
                UTF8_ENCODING,
                errors="replace",
            )

    diff_text = ""
    if candidate is not None:
        diff_text = build_gold_diff(
            previous_text=old_text,
            candidate_text=candidate.text,
            gold_path=gold_path,
            scenario_id=request.scenario_id,
        )

    if refusals:
        return GoldUpdatePlan(
            request=request,
            status=GoldUpdateStatus.REFUSED,
            gold_path=gold_path,
            candidate=candidate,
            previous_exists=previous_exists,
            previous_sha256=previous_sha256,
            candidate_sha256=candidate_sha256,
            diff_text=diff_text,
            refusals=tuple(refusals),
        )

    if previous_bytes == candidate_bytes:
        status = GoldUpdateStatus.UNCHANGED
    else:
        status = GoldUpdateStatus.READY

    return GoldUpdatePlan(
        request=request,
        status=status,
        gold_path=gold_path,
        candidate=candidate,
        previous_exists=previous_exists,
        previous_sha256=previous_sha256,
        candidate_sha256=candidate_sha256,
        diff_text=diff_text,
        refusals=(),
    )


def apply_gold_update(
    plan: GoldUpdatePlan,
    *,
    write_text: GoldUpdateWriter = atomic_write_text,
    read_bytes: BytesReader = Path.read_bytes,
    clock: Clock = lambda: datetime.now(UTC),
) -> GoldUpdateResult:
    if not isinstance(plan, GoldUpdatePlan):
        raise TypeError("plan must be a GoldUpdatePlan")
    if not callable(write_text):
        raise TypeError("write_text must be callable")
    if not callable(read_bytes):
        raise TypeError("read_bytes must be callable")
    if not callable(clock):
        raise TypeError("clock must be callable")

    if plan.status is GoldUpdateStatus.REFUSED:
        return GoldUpdateResult(
            status=GoldUpdateStatus.REFUSED,
            plan=plan,
        )
    if plan.status is GoldUpdateStatus.UNCHANGED:
        return GoldUpdateResult(
            status=GoldUpdateStatus.UNCHANGED,
            plan=plan,
        )
    if not plan.request.confirmed:
        return GoldUpdateResult(
            status=GoldUpdateStatus.DECLINED,
            plan=plan,
        )
    if not plan.request.diff_reviewed:
        refusal_plan = _refused_plan(
            plan,
            GoldUpdateRefusal(
                code=GoldUpdateRefusalCode.DIFF_NOT_REVIEWED,
                message=(
                    "gold update requires explicit review of the normalized diff before writing"
                ),
            ),
        )
        return GoldUpdateResult(
            status=GoldUpdateStatus.REFUSED,
            plan=refusal_plan,
        )
    if plan.candidate is None:
        raise GoldUpdateIntegrityError("ready gold update plan has no candidate")

    _ensure_no_concurrent_change(
        plan,
        read_bytes=read_bytes,
    )

    previous_bytes: bytes | None
    try:
        previous_bytes = read_bytes(plan.gold_path)
    except FileNotFoundError:
        previous_bytes = None
    except OSError as exc:
        raise GoldUpdateError(f"unable to read gold before update: {exc}") from exc

    try:
        write_text(
            plan.gold_path,
            plan.candidate.text,
            encoding=UTF8_ENCODING,
            newline="\n",
            create_parents=True,
            root=plan.request.gold_root,
            role="scenario gold file",
            sync=True,
            preserve_existing_mode=True,
        )
        written_bytes = read_bytes(plan.gold_path)
        written_sha256 = _sha256(written_bytes)

        if written_sha256 != plan.candidate_sha256:
            raise GoldUpdateIntegrityError("written gold SHA-256 does not match the candidate")

        written_text = written_bytes.decode(UTF8_ENCODING)
        parsed_written = parse_gold_document(
            written_text,
            expected_scenario_id=plan.request.scenario_id,
            expected_normalization_version=(plan.request.normalization_version),
        )
        if parsed_written.text != plan.candidate.text:
            raise GoldUpdateIntegrityError(
                "written gold content differs from the validated candidate"
            )
    except BaseException as exc:
        _restore_previous_gold(
            plan.gold_path,
            previous_bytes=previous_bytes,
            gold_root=plan.request.gold_root,
        )
        if isinstance(exc, GoldUpdateError):
            raise
        raise GoldUpdateError(f"gold update failed: {type(exc).__name__}: {exc}") from exc

    record = GoldUpdateRecord(
        scenario_id=plan.request.scenario_id,
        source_run_id=plan.request.source_run_id,
        gold_path=plan.gold_path,
        previous_sha256=plan.previous_sha256,
        new_sha256=written_sha256,
        normalization_version=(plan.request.normalization_version),
        reviewer=plan.request.reviewer,
        rationale=plan.request.rationale,
        decision_reference=plan.request.decision_reference,
        raw_stdout_path=plan.request.raw_stdout_path,
        raw_stderr_path=plan.request.raw_stderr_path,
        normalized_output_path=(plan.request.normalized_output_path),
        diff_evidence_path=plan.request.diff_evidence_path,
        updated_at=clock(),
        metadata=plan.request.metadata,
    )
    return GoldUpdateResult(
        status=GoldUpdateStatus.UPDATED,
        plan=plan,
        record=record,
    )


def update_gold(
    request: GoldUpdateRequest,
    *,
    write_text: GoldUpdateWriter = atomic_write_text,
    read_bytes: BytesReader = Path.read_bytes,
    clock: Clock = lambda: datetime.now(UTC),
) -> GoldUpdateResult:
    plan = prepare_gold_update(
        request,
        read_bytes=read_bytes,
    )
    return apply_gold_update(
        plan,
        write_text=write_text,
        read_bytes=read_bytes,
        clock=clock,
    )


def build_gold_diff(
    *,
    previous_text: str,
    candidate_text: str,
    gold_path: Path,
    scenario_id: ScenarioId | str,
) -> str:
    if not isinstance(previous_text, str):
        raise TypeError("previous_text must be a string")
    candidate_text = _canonical_text(
        candidate_text,
        field_name="candidate_text",
    )
    gold_path = _absolute_path(
        gold_path,
        field_name="gold_path",
    )
    scenario_id = validate_scenario_id(scenario_id)

    before_name = f"{gold_path.as_posix()}@previous" if previous_text else "/dev/null"
    after_name = f"{gold_path.as_posix()}@candidate"

    diff = "".join(
        unified_diff(
            previous_text.splitlines(keepends=True),
            candidate_text.splitlines(keepends=True),
            fromfile=before_name,
            tofile=after_name,
            lineterm="\n",
        )
    )
    header = f"# scenario_id: {scenario_id}\n# gold_path: {gold_path.as_posix()}\n"
    rendered = header + diff

    if len(rendered) > MAX_DIFF_CHARS:
        raise ValueError("gold diff exceeds the configured bounded size")
    return rendered


def serialize_gold_update_record(
    record: GoldUpdateRecord,
) -> str:
    if not isinstance(record, GoldUpdateRecord):
        raise TypeError("record must be a GoldUpdateRecord")
    return record.to_json()


def _request_refusals(
    request: GoldUpdateRequest,
) -> list[GoldUpdateRefusal]:
    refusals: list[GoldUpdateRefusal] = []

    if not request.markers_valid:
        refusals.append(
            GoldUpdateRefusal(
                code=GoldUpdateRefusalCode.MARKERS_INVALID,
                message=("required scenario markers were not verified"),
            )
        )
    if not request.normalization_succeeded:
        refusals.append(
            GoldUpdateRefusal(
                code=(GoldUpdateRefusalCode.NORMALIZATION_FAILED),
                message=("scenario normalization did not complete successfully"),
            )
        )
    if request.output_truncated:
        refusals.append(
            GoldUpdateRefusal(
                code=GoldUpdateRefusalCode.OUTPUT_TRUNCATED,
                message=("truncated scenario output cannot become gold"),
            )
        )
    if not request.output_complete:
        refusals.append(
            GoldUpdateRefusal(
                code=GoldUpdateRefusalCode.OUTPUT_INCOMPLETE,
                message=("incomplete scenario output cannot become gold"),
            )
        )
    if not request.compatibility_verified:
        refusals.append(
            GoldUpdateRefusal(
                code=(GoldUpdateRefusalCode.COMPATIBILITY_UNKNOWN),
                message=("GF/RGL compatibility must be verified before updating gold"),
            )
        )
    if not request.deterministic:
        refusals.append(
            GoldUpdateRefusal(
                code=GoldUpdateRefusalCode.NONDETERMINISTIC,
                message=("nondeterministic scenario output cannot become exact gold"),
            )
        )
    if not request.diff_reviewed:
        refusals.append(
            GoldUpdateRefusal(
                code=GoldUpdateRefusalCode.DIFF_NOT_REVIEWED,
                message=("normalized gold diff has not been explicitly reviewed"),
            )
        )

    meaningful = _has_meaningful_section_output(request.normalized_output_text)
    if not meaningful and not request.allow_empty:
        refusals.append(
            GoldUpdateRefusal(
                code=(GoldUpdateRefusalCode.OUTPUT_NOT_MEANINGFUL),
                message=(
                    "normalized output has no meaningful section "
                    "content and empty gold was not explicitly allowed"
                ),
            )
        )

    return refusals


def _validated_gold_path(
    request: GoldUpdateRequest,
) -> Path:
    gold_root = request.gold_root
    gold_path = request.gold_path

    try:
        contained = require_lexical_containment(
            gold_root,
            gold_path,
            role="scenario gold path",
            mode=ContainmentMode.STRICTLY_INSIDE,
        )
    except Exception as exc:
        raise GoldUpdateError(f"unsafe scenario gold path: {exc}") from exc

    expected_name = f"{request.scenario_id}{GOLD_SUFFIX}"
    if contained.name != expected_name:
        raise GoldUpdateError("gold filename must match the selected scenario ID")

    if contained.exists() and contained.is_symlink():
        raise GoldUpdateError("scenario gold path must not be a symbolic link")

    try:
        resolved_root = gold_root.resolve(strict=False)
        resolved_parent = contained.parent.resolve(strict=False)
        resolved_candidate = resolved_parent / contained.name
        resolved_candidate.relative_to(resolved_root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise GoldUpdateError("scenario gold path escapes the resolved gold root") from exc

    return contained


def _ensure_no_concurrent_change(
    plan: GoldUpdatePlan,
    *,
    read_bytes: BytesReader,
) -> None:
    try:
        current_bytes = read_bytes(plan.gold_path)
    except FileNotFoundError:
        current_bytes = None
    except OSError as exc:
        raise GoldUpdateError(f"unable to verify current gold before writing: {exc}") from exc

    current_sha256 = _sha256(current_bytes) if current_bytes is not None else None
    if current_sha256 != plan.previous_sha256:
        raise GoldUpdateConcurrentChangeError(
            "gold file changed after diff preparation; regenerate "
            "and review the diff before writing"
        )


def _restore_previous_gold(
    gold_path: Path,
    *,
    previous_bytes: bytes | None,
    gold_root: Path,
) -> None:
    try:
        if previous_bytes is None:
            gold_path.unlink(missing_ok=True)
        else:
            atomic_write_bytes(
                gold_path,
                previous_bytes,
                create_parents=True,
                root=gold_root,
                role="scenario gold rollback",
                sync=True,
                preserve_existing_mode=True,
            )
    except OSError as rollback_error:
        raise GoldUpdateIntegrityError(
            f"gold update failed and rollback could not restore the previous file: {rollback_error}"
        ) from rollback_error


def _refused_plan(
    plan: GoldUpdatePlan,
    refusal: GoldUpdateRefusal,
) -> GoldUpdatePlan:
    return GoldUpdatePlan(
        request=plan.request,
        status=GoldUpdateStatus.REFUSED,
        gold_path=plan.gold_path,
        candidate=plan.candidate,
        previous_exists=plan.previous_exists,
        previous_sha256=plan.previous_sha256,
        candidate_sha256=plan.candidate_sha256,
        diff_text=plan.diff_text,
        refusals=(refusal,),
    )


def _validate_sections(
    lines: list[str],
) -> tuple[str, ...]:
    sections: list[str] = []
    seen: set[str] = set()
    index = 0

    while index < len(lines):
        line = lines[index]
        if not line:
            index += 1
            continue

        begin = _SECTION_BEGIN_RE.fullmatch(line)
        if begin is None:
            raise ValueError("gold/output body must contain only canonical BEGIN/END sections")

        section = begin.group("section")
        if section in seen:
            raise ValueError(f"duplicate section ID {section!r}")

        end_index = index + 1
        while end_index < len(lines):
            end = _SECTION_END_RE.fullmatch(lines[end_index])
            if end is not None:
                if end.group("section") != section:
                    raise ValueError(f"section END marker does not match BEGIN marker {section!r}")
                break
            nested = _SECTION_BEGIN_RE.fullmatch(lines[end_index])
            if nested is not None:
                raise ValueError("nested scenario sections are prohibited")
            end_index += 1

        if end_index >= len(lines):
            raise ValueError(f"section {section!r} has no matching END marker")

        seen.add(section)
        sections.append(section)
        index = end_index + 1

    if not sections:
        raise ValueError("gold/output document must contain at least one section")

    return tuple(sections)


def _has_meaningful_section_output(text: str) -> bool:
    try:
        canonical = _canonical_text(
            text,
            field_name="normalized output",
        )
    except (TypeError, ValueError):
        return False

    lines = canonical.splitlines()
    if len(lines) < 4:
        return False

    in_section = False
    for line in lines[3:]:
        if _SECTION_BEGIN_RE.fullmatch(line):
            in_section = True
            continue
        if _SECTION_END_RE.fullmatch(line):
            in_section = False
            continue
        if in_section and line.strip():
            return True
    return False


def _section_tuple(
    values: object,
) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise TypeError("sections must be a tuple")

    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        section = validate_scenario_id(
            value,
            field="section ID",
        )
        text = str(section)
        if text in seen:
            raise ValueError(f"duplicate section ID {text!r}")
        seen.add(text)
        result.append(text)

    if not result:
        raise ValueError("sections must not be empty")
    return tuple(result)


def _header_value(
    line: str,
    *,
    prefix: str,
    field_name: str,
) -> str:
    if not line.startswith(prefix):
        raise ValueError(f"missing canonical {field_name} header")
    return _required_text(
        line[len(prefix) :],
        field_name=field_name,
    )


def _canonical_text(
    value: object,
    *,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if "\x00" in value:
        raise ValueError(f"{field_name} must not contain NUL characters")
    if value.startswith("\ufeff"):
        value = value.removeprefix("\ufeff")
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    if not value.endswith("\n"):
        value += "\n"
    return value


def _validate_version(
    value: object,
    *,
    field_name: str,
) -> str:
    text = _required_text(value, field_name=field_name)
    if _VERSION_RE.fullmatch(text) is None:
        raise ValueError(f"{field_name} must be a dotted numeric version")
    return text


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _required_sha256(
    value: object,
    *,
    field_name: str,
) -> str:
    result = _optional_sha256(
        value,
        field_name=field_name,
    )
    if result is None:
        raise ValueError(f"{field_name} must not be None")
    return result


def _optional_sha256(
    value: object,
    *,
    field_name: str,
) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string or None")
    if len(value) != SHA256_HEX_LENGTH:
        raise ValueError(
            f"{field_name} must contain exactly {SHA256_HEX_LENGTH} hexadecimal digits"
        )
    if value.lower() != value:
        raise ValueError(f"{field_name} must use lowercase hexadecimal digits")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must contain only hexadecimal digits")
    return value


def _string_mapping(
    value: object,
    *,
    field_name: str,
) -> Mapping[str, str]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a mapping")

    normalized: dict[str, str] = {}
    for key, item in value.items():
        normalized_key = _required_text(
            key,
            field_name=f"{field_name} key",
        )
        normalized_value = _bounded_text(
            item,
            field_name=f"{field_name}[{normalized_key!r}]",
        )
        normalized[normalized_key] = normalized_value

    return MappingProxyType(dict(sorted(normalized.items())))


def _bounded_text(
    value: object,
    *,
    field_name: str,
) -> str:
    text = _required_text(value, field_name=field_name)
    if len(text) > MAX_RECORD_TEXT_CHARS:
        raise ValueError(f"{field_name} exceeds the bounded text limit")
    return text


def _required_text(
    value: object,
    *,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if "\x00" in value:
        raise ValueError(f"{field_name} must not contain NUL characters")
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must not have outer whitespace")
    return value


def _absolute_path(
    value: object,
    *,
    field_name: str,
) -> Path:
    if not isinstance(value, Path):
        raise TypeError(f"{field_name} must be a pathlib.Path")
    if "\x00" in str(value):
        raise ValueError(f"{field_name} must not contain NUL characters")
    if not value.is_absolute():
        raise ValueError(f"{field_name} must be absolute")
    return value


def _optional_absolute_path(
    value: object,
    *,
    field_name: str,
) -> Path | None:
    if value is None:
        return None
    return _absolute_path(
        value,
        field_name=field_name,
    )


def _utc_datetime(
    value: object,
    *,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


__all__ = (
    "GOLD_DIRECTORY_PARTS",
    "GOLD_SCHEMA_HEADER",
    "GOLD_SUFFIX",
    "OUTPUT_SCHEMA_HEADER",
    "GoldDocument",
    "GoldUpdateConcurrentChangeError",
    "GoldUpdateError",
    "GoldUpdateIntegrityError",
    "GoldUpdatePlan",
    "GoldUpdateRecord",
    "GoldUpdateRefusal",
    "GoldUpdateRefusalCode",
    "GoldUpdateRequest",
    "GoldUpdateResult",
    "GoldUpdateStatus",
    "apply_gold_update",
    "build_gold_diff",
    "parse_gold_document",
    "parse_normalized_output_document",
    "prepare_gold_update",
    "serialize_gold_update_record",
    "update_gold",
)
